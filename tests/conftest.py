"""Fixtures compartidas."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric import ec


@pytest.fixture
def fixed_timestamp() -> datetime:
    return datetime(2026, 9, 13, 12, 0, 0, 123000, tzinfo=timezone.utc)


@pytest.fixture
def sample_payload() -> bytes:
    return b"hello evidence"


@pytest.fixture
def ec_keypair() -> tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
    private = ec.generate_private_key(ec.SECP256R1())
    return private, private.public_key()


@pytest.fixture
def kms_key() -> bytes:
    return b"\x01" * 32
