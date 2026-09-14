"""Smoke tests de firma JWS detached RFC 7797."""

from __future__ import annotations

import pytest

from src.core.errors import AlgorithmNotAllowedError, InvalidSignatureError, JwsError
from src.core.jws import sign_detached, verify_detached

KID = "test-kid-001"
X5C = ["MIIB...test..."]


def test_sign_and_verify_roundtrip(ec_keypair, sample_payload: bytes) -> None:
    private, public = ec_keypair
    jws = sign_detached(sample_payload, private, KID, X5C)
    assert jws["payload"] == ""
    verify_detached(jws, sample_payload, public)


def test_rejects_payload_inline(ec_keypair, sample_payload: bytes) -> None:
    private, public = ec_keypair
    jws = sign_detached(sample_payload, private, KID, X5C)
    jws["payload"] = "aGVsbG8="
    with pytest.raises(JwsError):
        verify_detached(jws, sample_payload, public)


def test_rejects_tampered_payload(ec_keypair, sample_payload: bytes) -> None:
    private, public = ec_keypair
    jws = sign_detached(sample_payload, private, KID, X5C)
    with pytest.raises(InvalidSignatureError):
        verify_detached(jws, b"tampered", public)


def test_rejects_alg_none(ec_keypair, sample_payload: bytes) -> None:
    import base64
    import json

    protected = {
        "alg": "none",
        "b64": False,
        "crit": ["b64"],
        "cty": "application/json",
        "kid": KID,
        "x5c": X5C,
    }
    b64 = base64.urlsafe_b64encode(
        json.dumps(protected, separators=(",", ":")).encode()
    ).rstrip(b"=").decode()
    jws = {"payload": "", "protected": b64, "signature": "AAAA"}
    with pytest.raises(AlgorithmNotAllowedError):
        verify_detached(jws, sample_payload, ec_keypair[1])


def test_rejects_alg_not_allowed(ec_keypair, sample_payload: bytes) -> None:
    private, _ = ec_keypair
    with pytest.raises(AlgorithmNotAllowedError):
        sign_detached(sample_payload, private, KID, X5C, alg="HS256")


def test_rejects_missing_x5c(ec_keypair, sample_payload: bytes) -> None:
    private, _ = ec_keypair
    with pytest.raises(JwsError):
        sign_detached(sample_payload, private, KID, [])
