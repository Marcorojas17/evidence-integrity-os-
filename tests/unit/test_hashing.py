"""Smoke tests de hashing y compromiso HMAC."""

from __future__ import annotations

import hashlib

import pytest

from src.core.errors import HashingError
from src.core.hashing import (
    constant_time_eq,
    content_hash_bytes,
    content_hash_hex,
    private_commitment,
)


def test_content_hash_matches_hashlib(sample_payload: bytes) -> None:
    expected = hashlib.sha256(sample_payload).hexdigest()
    assert content_hash_hex(sample_payload) == expected


def test_content_hash_bytes_returns_32_bytes(sample_payload: bytes) -> None:
    assert len(content_hash_bytes(sample_payload)) == 32


def test_content_hash_rejects_non_bytes() -> None:
    with pytest.raises(HashingError):
        content_hash_bytes("no bytes")  # type: ignore[arg-type]


def test_private_commitment_deterministic(kms_key: bytes, sample_payload: bytes) -> None:
    ch = content_hash_bytes(sample_payload)
    a = private_commitment(kms_key, "ctx_test_001", ch)
    b = private_commitment(kms_key, "ctx_test_001", ch)
    assert a == b
    assert len(a) == 32


def test_private_commitment_changes_with_context(kms_key: bytes, sample_payload: bytes) -> None:
    ch = content_hash_bytes(sample_payload)
    a = private_commitment(kms_key, "ctx_a", ch)
    b = private_commitment(kms_key, "ctx_b", ch)
    assert a != b


def test_private_commitment_requires_key(sample_payload: bytes) -> None:
    ch = content_hash_bytes(sample_payload)
    with pytest.raises(HashingError):
        private_commitment(b"", "ctx", ch)


def test_constant_time_eq_ok() -> None:
    assert constant_time_eq(b"abc", b"abc")
    assert not constant_time_eq(b"abc", b"abd")
    assert not constant_time_eq(b"abc", b"abcd")
