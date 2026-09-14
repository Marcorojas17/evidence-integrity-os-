"""Smoke tests de cliente RFC 3161."""

from __future__ import annotations

import pytest

from src.core.errors import EvidenceError
from src.core.timestamp import (
    TimestampError,
    request_timestamp,
    verify_token_imprint,
)


def test_rejects_empty_url() -> None:
    with pytest.raises(TimestampError):
        request_timestamp("", b"\x00" * 32)


def test_rejects_non_32_byte_digest() -> None:
    with pytest.raises(EvidenceError):
        request_timestamp("https://example.invalid", b"\x00" * 16)


def test_imprint_mismatch_raises() -> None:
    # Token ASN.1 de estructura invalida debe fallar al parsear.
    with pytest.raises(TimestampError):
        verify_token_imprint(b"not-a-token", b"\x00" * 32)
