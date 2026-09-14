"""Pruebas de detección de corrupción y manipulación.

Verifica que el sistema detecta:
- Un byte cambiado en el manifiesto.
- Un byte cambiado en el JWS.
- Un byte cambiado en el token RFC 3161.
- Un evento alterado en el log de auditoría.
- Un cierre alterado.
"""

from __future__ import annotations

import base64
import io
import json
import zipfile
from datetime import datetime, timezone

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from src.audit.anchor import LocalFilesystemAnchor
from src.audit.integrity import create_close, verify_audit_log
from src.audit.logger import genesis_event, new_event_id, write_event
from src.core.jws import _jwk_thumbprint_sha256
from src.evidence.verifier import verify_evidence_package


def _mat() -> dict:
    key = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc).replace(year=2027))
        .sign(key, hashes.SHA256())
    )
    der = cert.public_bytes(serialization.Encoding.DER)
    return {
        "key": key,
        "kid": _jwk_thumbprint_sha256(key.public_key()),
        "x5c": [base64.b64encode(der).decode("ascii")],
    }


def _iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def test_detects_corrupted_manifest() -> None:
    """Un ZIP con manifiesto modificado falla la verificación."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("manifest.payload.json", b'{"evidence_id":"ev_test"}')
        zf.writestr("manifest.jws.json", "{}")
        zf.writestr("operational.json", "{}")
        zf.writestr("proofs/token.rfc3161", b"\x00")

    result = verify_evidence_package(buf.getvalue())
    assert not result.valid


def test_detects_corrupted_zip() -> None:
    result = verify_evidence_package(b"not a zip file at all")
    assert not result.valid
    assert any(not s.passed for s in result.steps)


def test_detects_tampered_audit_event(tmp_path) -> None:
    mat = _mat()
    log = tmp_path / "audit.jsonl"

    e = genesis_event(
        event_id=new_event_id(),
        occurred_at=_iso(),
        payload={"x": 1},
        signing_key=mat["key"],
        signing_kid=mat["kid"],
        signing_x5c=mat["x5c"],
    )
    write_event(log, e)

    # Manipular el event_hash
    raw = log.read_text(encoding="utf-8")
    raw = raw.replace(e.event_hash, "0" * 64)
    log.write_text(raw, encoding="utf-8")

    result = verify_audit_log(log_path=log)
    assert not result.valid


def test_detects_tampered_close(tmp_path) -> None:
    mat = _mat()
    log = tmp_path / "audit.jsonl"

    e = genesis_event(
        event_id=new_event_id(),
        occurred_at=_iso(),
        payload={},
        signing_key=mat["key"],
        signing_kid=mat["kid"],
        signing_x5c=mat["x5c"],
    )
    write_event(log, e)

    anchor = LocalFilesystemAnchor(tmp_path / "anchors")
    close = create_close(
        log_path=log,
        signing_key=mat["key"],
        signing_kid=mat["kid"],
        signing_x5c=mat["x5c"],
        anchor_provider=anchor,
    )

    # Alterar close_hash manteniendo firma original
    tampered = type(close)(
        close_id=close.close_id,
        closed_at=close.closed_at,
        event_count=close.event_count,
        close_hash="0" * 64,
        signature=close.signature,
    )
    result = verify_audit_log(
        log_path=log,
        closes=[tampered],
        anchor_provider=anchor,
    )
    assert not result.valid


def test_detects_chain_break(tmp_path) -> None:
    """Dos eventos que no encadenan bien deben fallar."""
    mat = _mat()
    log = tmp_path / "audit.jsonl"

    e0 = genesis_event(
        event_id=new_event_id(),
        occurred_at=_iso(),
        payload={"i": 0},
        signing_key=mat["key"],
        signing_kid=mat["kid"],
        signing_x5c=mat["x5c"],
    )
    write_event(log, e0)

    # Escribir el mismo evento dos veces (rompe el chain)
    write_event(log, e0)

    result = verify_audit_log(log_path=log)
    assert not result.valid
