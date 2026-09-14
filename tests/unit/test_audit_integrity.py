"""Smoke tests de cierres y verificacion."""

from __future__ import annotations

import base64
from datetime import datetime, timezone

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from src.audit.anchor import LocalFilesystemAnchor
from src.audit.integrity import (
    create_close,
    read_closes,
    verify_audit_log,
    write_close,
)
from src.audit.logger import (
    append_event,
    genesis_event,
    new_event_id,
    write_event,
)
from src.core.jws import _jwk_thumbprint_sha256


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


def _make_log(path, n: int = 3) -> None:
    mat = _mat()
    e = genesis_event(
        event_id=new_event_id(),
        occurred_at=_iso(),
        payload={"i": 0},
        signing_key=mat["key"],
        signing_kid=mat["kid"],
        signing_x5c=mat["x5c"],
    )
    write_event(path, e)
    for i in range(1, n):
        e = append_event(
            e,
            event_id=new_event_id(),
            occurred_at=_iso(),
            event_type="action",
            payload={"i": i},
            signing_key=mat["key"],
            signing_kid=mat["kid"],
            signing_x5c=mat["x5c"],
        )
        write_event(path, e)


def test_verify_log_without_closes(tmp_path) -> None:
    log = tmp_path / "audit.jsonl"
    _make_log(log, n=3)
    result = verify_audit_log(log_path=log)
    assert result.valid
    assert result.event_count == 3


def test_create_close_and_verify(tmp_path) -> None:
    mat = _mat()
    log = tmp_path / "audit.jsonl"
    _make_log(log, n=3)

    anchor = LocalFilesystemAnchor(tmp_path / "anchors")
    close = create_close(
        log_path=log,
        signing_key=mat["key"],
        signing_kid=mat["kid"],
        signing_x5c=mat["x5c"],
        anchor_provider=anchor,
    )

    closes_path = tmp_path / "closes.jsonl"
    write_close(closes_path, close)
    closes = read_closes(closes_path)
    assert len(closes) == 1

    result = verify_audit_log(
        log_path=log,
        closes=closes,
        anchor_provider=anchor,
    )
    assert result.valid
    assert result.close_count == 1


def test_detects_tampered_event(tmp_path) -> None:
    log = tmp_path / "audit.jsonl"
    _make_log(log, n=3)
    # Corrompe el hash del primer evento
    content = log.read_text(encoding="utf-8").splitlines()
    content[0] = content[0].replace('"event_hash":"', '"event_hash":"0')
    log.write_text("\n".join(content) + "\n", encoding="utf-8")

    result = verify_audit_log(log_path=log)
    assert not result.valid
    assert any(not s.passed for s in result.steps)


def test_detects_tampered_close(tmp_path) -> None:
    mat = _mat()
    log = tmp_path / "audit.jsonl"
    _make_log(log, n=3)
    anchor = LocalFilesystemAnchor(tmp_path / "anchors")
    close = create_close(
        log_path=log,
        signing_key=mat["key"],
        signing_kid=mat["kid"],
        signing_x5c=mat["x5c"],
        anchor_provider=anchor,
    )
    # Corrompe el close_hash pero mantiene la firma original
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
