"""Smoke tests JWS RFC 7797 con casos negativos completos."""

from __future__ import annotations

import base64
import json

import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

from src.core.errors import AlgorithmNotAllowedError, InvalidSignatureError, JwsError
from src.core.jws import sign_detached, verify_detached


def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


@pytest.fixture
def fake_x5c() -> list[str]:
    """Un certificado X.509 autofirmado real para pruebas."""
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from datetime import datetime, timedelta, timezone
    from cryptography.hazmat.primitives import hashes

    key = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc) - timedelta(days=1))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    der = cert.public_bytes(serialization.Encoding.DER)
    return [base64.b64encode(der).decode("ascii")]


def test_roundtrip(fake_x5c: list[str]) -> None:
    private = ec.generate_private_key(ec.SECP256R1())
    payload = b"hello"
    from src.core.jws import _jwk_thumbprint_sha256
    kid = _jwk_thumbprint_sha256(private.public_key())
    jws = sign_detached(payload, private, kid, fake_x5c)
    verify_detached(jws, payload)


def test_rejects_missing_kid(fake_x5c: list[str]) -> None:
    private = ec.generate_private_key(ec.SECP256R1())
    with pytest.raises(JwsError):
        sign_detached(b"x", private, "", fake_x5c)


def test_rejects_missing_x5c() -> None:
    private = ec.generate_private_key(ec.SECP256R1())
    with pytest.raises(JwsError):
        sign_detached(b"x", private, "some-kid", [])


def test_rejects_alg_none(sample_payload: bytes, fake_x5c: list[str]) -> None:
    protected = {
        "alg": "none",
        "b64": False,
        "crit": ["b64"],
        "cty": "application/json",
        "kid": "x",
        "x5c": fake_x5c,
    }
    jws = {
        "payload": "",
        "protected": _b64u(json.dumps(protected, separators=(",", ":")).encode()),
        "signature": _b64u(b"0" * 64),
    }
    with pytest.raises(AlgorithmNotAllowedError):
        verify_detached(jws, sample_payload)


def test_rejects_alg_not_allowed(fake_x5c: list[str]) -> None:
    private = ec.generate_private_key(ec.SECP256R1())
    with pytest.raises(AlgorithmNotAllowedError):
        sign_detached(b"x", private, "kid", fake_x5c, alg="HS256")


def test_rejects_invalid_crit(sample_payload: bytes, fake_x5c: list[str]) -> None:
    protected = {
        "alg": "ES256",
        "b64": False,
        "crit": [],
        "cty": "application/json",
        "kid": "x",
        "x5c": fake_x5c,
    }
    jws = {
        "payload": "",
        "protected": _b64u(json.dumps(protected, separators=(",", ":")).encode()),
        "signature": _b64u(b"0" * 64),
    }
    with pytest.raises(JwsError):
        verify_detached(jws, sample_payload)


def test_rejects_truncated_signature(fake_x5c: list[str]) -> None:
    private = ec.generate_private_key(ec.SECP256R1())
    from src.core.jws import _jwk_thumbprint_sha256
    kid = _jwk_thumbprint_sha256(private.public_key())
    jws = sign_detached(b"x", private, kid, fake_x5c)
    jws["signature"] = _b64u(b"\x00" * 32)
    with pytest.raises(JwsError):
        verify_detached(jws, b"x")


def test_rejects_kid_not_matching_cert(fake_x5c: list[str]) -> None:
    private = ec.generate_private_key(ec.SECP256R1())
    jws = sign_detached(b"x", private, "wrong-kid", fake_x5c)
    with pytest.raises(JwsError):
        verify_detached(jws, b"x")


def test_rejects_tampered_payload(fake_x5c: list[str]) -> None:
    private = ec.generate_private_key(ec.SECP256R1())
    from src.core.jws import _jwk_thumbprint_sha256
    kid = _jwk_thumbprint_sha256(private.public_key())
    jws = sign_detached(b"original", private, kid, fake_x5c)
    with pytest.raises(InvalidSignatureError):
        verify_detached(jws, b"tampered")


def test_trust_store_invoked(fake_x5c: list[str]) -> None:
    private = ec.generate_private_key(ec.SECP256R1())
    from src.core.jws import _jwk_thumbprint_sha256
    kid = _jwk_thumbprint_sha256(private.public_key())
    jws = sign_detached(b"x", private, kid, fake_x5c)

    called: list[int] = []
    def ts(certs):  # noqa: ANN001
        called.append(len(certs))

    verify_detached(jws, b"x", trust_store=ts)
    assert called == [1]
