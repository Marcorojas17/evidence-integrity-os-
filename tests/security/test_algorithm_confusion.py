"""Pruebas de confusión de algoritmos en JWS.

Casos:
- alg=none debe rechazarse.
- Algoritmos fuera de allowlist deben rechazarse.
- HS256 con clave pública no debe aceptarse.
- b64=true (payload embebido) no debe aceptarse como detached.
- crit vacío o sin b64 debe rechazarse.
"""

from __future__ import annotations

import base64
import json

import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from src.core.errors import AlgorithmNotAllowedError, JwsError
from src.core.jws import sign_detached, verify_detached


def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _fake_x5c() -> list[str]:
    """Certificado X.509 autofirmado mínimo en DER base64."""
    from datetime import datetime, timedelta, timezone

    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.x509.oid import NameOID

    key = ec.generate_private_key(ec.SECP256R1())
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
        .sign(key, hashes.SHA256())
    )
    der = cert.public_bytes(serialization.Encoding.DER)
    return [base64.b64encode(der).decode("ascii")]


def _build_jws(protected: dict, payload: bytes = b"x") -> dict:
    protected_b64 = _b64u(json.dumps(protected, separators=(",", ":")).encode())
    return {
        "payload": "",
        "protected": protected_b64,
        "signature": _b64u(b"\x00" * 64),
    }


def test_rejects_alg_none() -> None:
    jws = _build_jws(
        {
            "alg": "none",
            "b64": False,
            "crit": ["b64"],
            "cty": "application/json",
            "kid": "x",
            "x5c": _fake_x5c(),
        }
    )
    with pytest.raises(AlgorithmNotAllowedError):
        verify_detached(jws, b"x")


@pytest.mark.parametrize("alg", ["HS256", "RS256", "ES384", "ES512", "PS256", "none"])
def test_rejects_disallowed_algorithms(alg: str) -> None:
    jws = _build_jws(
        {
            "alg": alg,
            "b64": False,
            "crit": ["b64"],
            "cty": "application/json",
            "kid": "x",
            "x5c": _fake_x5c(),
        }
    )
    with pytest.raises(AlgorithmNotAllowedError):
        verify_detached(jws, b"x")


def test_rejects_b64_true() -> None:
    jws = _build_jws(
        {
            "alg": "ES256",
            "b64": True,
            "crit": ["b64"],
            "cty": "application/json",
            "kid": "x",
            "x5c": _fake_x5c(),
        }
    )
    with pytest.raises(JwsError):
        verify_detached(jws, b"x")


def test_rejects_missing_b64_in_crit() -> None:
    jws = _build_jws(
        {
            "alg": "ES256",
            "b64": False,
            "crit": [],
            "cty": "application/json",
            "kid": "x",
            "x5c": _fake_x5c(),
        }
    )
    with pytest.raises(JwsError):
        verify_detached(jws, b"x")


def test_rejects_payload_inline() -> None:
    jws = {
        "payload": "aGVsbG8=",
        "protected": _b64u(json.dumps({
            "alg": "ES256",
            "b64": False,
            "crit": ["b64"],
            "cty": "application/json",
            "kid": "x",
            "x5c": _fake_x5c(),
        }, separators=(",", ":")).encode()),
        "signature": _b64u(b"\x00" * 64),
    }
    with pytest.raises(JwsError):
        verify_detached(jws, b"x")


def test_sign_rejects_disallowed_alg() -> None:
    key = ec.generate_private_key(ec.SECP256R1())
    with pytest.raises(AlgorithmNotAllowedError):
        sign_detached(b"x", key, "kid", _fake_x5c(), alg="HS256")
