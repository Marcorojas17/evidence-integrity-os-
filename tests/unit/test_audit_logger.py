"""Smoke tests del log encadenado."""

from __future__ import annotations

import base64
from datetime import datetime, timezone

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

from src.audit.errors import AuditError
from src.audit.logger import (
    append_event,
    genesis_event,
    new_event_id,
    read_events,
    write_event,
)
from src.core.jws import _jwk_thumbprint_sha256


def _signing_material() -> dict:
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


def test_genesis_has_empty_prev_hash() -> None:
    mat = _signing_material()
    e = genesis_event(
        event_id=new_event_id(),
        occurred_at=_iso(),
        payload={"a": 1},
        signing_key=mat["key"],
        signing_kid=mat["kid"],
        signing_x5c=mat["x5c"],
    )
    assert e.prev_event_hash == ""
    assert e.event_hash == e.compute_hash()


def test_append_chains_hashes() -> None:
    mat = _signing_material()
    e0 = genesis_event(
        event_id=new_event_id(),
        occurred_at=_iso(),
        payload={"a": 1},
        signing_key=mat["key"],
        signing_kid=mat["kid"],
        signing_x5c=mat["x5c"],
    )
    e1 = append_event(
        e0,
        event_id=new_event_id(),
        occurred_at=_iso(),
        event_type="action",
        payload={"b": 2},
        signing_key=mat["key"],
        signing_kid=mat["kid"],
        signing_x5c=mat["x5c"],
    )
    assert e1.prev_event_hash == e0.event_hash
    assert e1.event_hash != e0.event_hash


def test_append_rejects_genesis_event_type() -> None:
    mat = _signing_material()
    e0 = genesis_event(
        event_id=new_event_id(),
        occurred_at=_iso(),
        payload={},
        signing_key=mat["key"],
        signing_kid=mat["kid"],
        signing_x5c=mat["x5c"],
    )
    with pytest.raises(AuditError):
        append_event(
            e0,
            event_id=new_event_id(),
            occurred_at=_iso(),
            event_type="genesis",
            payload={},
            signing_key=mat["key"],
            signing_kid=mat["kid"],
            signing_x5c=mat["x5c"],
        )


def test_write_and_read_roundtrip(tmp_path) -> None:
    mat = _signing_material()
    path = tmp_path / "audit.jsonl"
    e0 = genesis_event(
        event_id=new_event_id(),
        occurred_at=_iso(),
        payload={"a": 1},
        signing_key=mat["key"],
        signing_kid=mat["kid"],
        signing_x5c=mat["x5c"],
    )
    e1 = append_event(
        e0,
        event_id=new_event_id(),
        occurred_at=_iso(),
        event_type="action",
        payload={"b": 2},
        signing_key=mat["key"],
        signing_kid=mat["kid"],
        signing_x5c=mat["x5c"],
    )
    write_event(path, e0)
    write_event(path, e1)
    events = read_events(path)
    assert len(events) == 2
    assert events[0].event_hash == e0.event_hash
    assert events[1].prev_event_hash == e0.event_hash


def test_read_missing_file_raises(tmp_path) -> None:
    with pytest.raises(AuditError):
        read_events(tmp_path / "no-existe.jsonl")
