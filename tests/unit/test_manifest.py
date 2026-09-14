"""Smoke tests del manifiesto v1."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.core.errors import ManifestError, ManifestValidationError
from src.core.manifest import (
    Chain,
    Commitment,
    Content,
    Manifest,
)


def _valid_manifest() -> Manifest:
    return Manifest(
        evidence_id="ev_abc12345",
        created_at=datetime(2026, 9, 13, 12, 0, 0, 123000, tzinfo=timezone.utc),
        content=Content(
            content_hash="a" * 64,
            size_bytes="1024",
            mime_type="image/jpeg",
        ),
        commitment=Commitment(
            context_id="ctx_test_001",
            private_commitment="b" * 64,
            kms_key_id="kms-hmac-v1",
        ),
        chain=Chain(
            previous_manifest_hash="",
            chain_position="0",
        ),
        original_included=False,
    )


def test_payload_has_required_fields() -> None:
    p = _valid_manifest().to_payload()
    assert p["$schema"] == "urn:evidence-integrity:manifest:v1"
    assert p["manifest_version"] == "1.0"
    assert p["content"]["hash_algorithm"] == "sha256"
    assert p["commitment"]["algorithm"] == "hmac-sha256"


def test_canonical_bytes_are_deterministic() -> None:
    m = _valid_manifest()
    assert m.canonical_bytes() == m.canonical_bytes()


def test_validate_passes_for_valid_manifest() -> None:
    _valid_manifest().validate()


def test_rejects_bad_evidence_id() -> None:
    m = _valid_manifest()
    object.__setattr__(m, "evidence_id", "bad_id")
    with pytest.raises(ManifestValidationError):
        m.validate()


def test_rejects_short_hash() -> None:
    m = _valid_manifest()
    object.__setattr__(
        m,
        "content",
        Content(content_hash="a" * 10, size_bytes="1", mime_type="text/plain"),
    )
    with pytest.raises(ManifestValidationError):
        m.validate()


def test_rejects_naive_datetime() -> None:
    m = _valid_manifest()
    object.__setattr__(
        m, "created_at", datetime(2026, 9, 13, 12, 0, 0)
    )
    with pytest.raises(ManifestError):
        m.to_payload()
