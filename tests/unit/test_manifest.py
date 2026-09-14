"""Smoke tests del manifiesto v1 con validacion contra esquema."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.core.errors import ManifestError, ManifestValidationError
from src.core.manifest import Chain, Commitment, Content, Manifest


def _valid() -> Manifest:
    return Manifest(
        evidence_id="ev_abc12345",
        created_at=datetime(2026, 9, 13, 12, 0, 0, 123000, tzinfo=timezone.utc),
        content=Content(content_hash="a" * 64, size_bytes="1024", mime_type="image/jpeg"),
        commitment=Commitment(
            context_id="ctx_test_001",
            private_commitment="b" * 64,
            kms_key_id="kms-hmac-v1",
        ),
        chain=Chain(previous_manifest_hash="", chain_position="0"),
    )


def test_valid_manifest_passes_schema() -> None:
    _valid().validate()


def test_rejects_bad_evidence_id() -> None:
    m = _valid()
    object.__setattr__(m, "evidence_id", "bad_id")
    with pytest.raises(ManifestValidationError):
        m.validate()


def test_rejects_short_hash() -> None:
    m = _valid()
    object.__setattr__(m, "content", Content("a" * 10, "1", "text/plain"))
    with pytest.raises(ManifestValidationError):
        m.validate()


def test_rejects_uppercase_hash() -> None:
    m = _valid()
    object.__setattr__(m, "content", Content("A" * 64, "1", "text/plain"))
    with pytest.raises(ManifestValidationError):
        m.validate()


def test_rejects_non_numeric_size() -> None:
    m = _valid()
    object.__setattr__(m, "content", Content("a" * 64, "1024 bytes", "text/plain"))
    with pytest.raises(ManifestValidationError):
        m.validate()


def test_rejects_naive_datetime() -> None:
    m = _valid()
    object.__setattr__(m, "created_at", datetime(2026, 9, 13, 12, 0, 0))
    with pytest.raises(ManifestError):
        m.to_payload()


def test_rejects_chain_position_zero_with_prev_hash() -> None:
    m = _valid()
    object.__setattr__(
        m, "chain", Chain(previous_manifest_hash="c" * 64, chain_position="0")
    )
    with pytest.raises(ManifestValidationError):
        m.validate()


def test_rejects_nonzero_position_without_prev_hash() -> None:
    m = _valid()
    object.__setattr__(m, "chain", Chain(previous_manifest_hash="", chain_position="1"))
    with pytest.raises(ManifestValidationError):
        m.validate()
