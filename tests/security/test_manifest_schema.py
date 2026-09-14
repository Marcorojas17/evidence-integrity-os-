"""Pruebas de validación contra el esquema JSON del manifiesto."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
import pytest

from src.core.errors import ManifestValidationError
from src.core.manifest import Chain, Commitment, Content, Manifest

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "schemas"
    / "manifest-v1.schema.json"
)


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _base() -> Manifest:
    return Manifest(
        evidence_id="ev_abc12345",
        created_at=datetime(2026, 9, 13, 12, 0, 0, tzinfo=timezone.utc),
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
        chain=Chain(previous_manifest_hash="", chain_position="0"),
    )


def test_schema_loads(schema: dict) -> None:
    assert schema["$id"] == "urn:evidence-integrity:manifest:v1"


def test_valid_manifest_matches_schema(schema: dict) -> None:
    jsonschema.validate(_base().to_payload(), schema)


def test_rejects_extra_field(schema: dict) -> None:
    payload = _base().to_payload()
    payload["extra"] = "no permitido"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)


def test_rejects_missing_field(schema: dict) -> None:
    payload = _base().to_payload()
    del payload["commitment"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)


def test_rejects_invalid_evidence_id(schema: dict) -> None:
    payload = _base().to_payload()
    payload["evidence_id"] = "bad_id"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)


def test_rejects_uppercase_hash(schema: dict) -> None:
    payload = _base().to_payload()
    payload["content"]["content_hash"] = "A" * 64
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)


def test_rejects_float_size(schema: dict) -> None:
    payload = _base().to_payload()
    payload["content"]["size_bytes"] = 1024
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)


def test_rejects_unknown_algorithm(schema: dict) -> None:
    payload = _base().to_payload()
    payload["content"]["hash_algorithm"] = "md5"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)


def test_internal_validation_chain_position_zero() -> None:
    m = _base()
    object.__setattr__(
        m, "chain", Chain(previous_manifest_hash="c" * 64, chain_position="0")
    )
    with pytest.raises(ManifestValidationError):
        m.validate()


def test_internal_validation_nonzero_without_prev() -> None:
    m = _base()
    object.__setattr__(
        m, "chain", Chain(previous_manifest_hash="", chain_position="1")
    )
    with pytest.raises(ManifestValidationError):
        m.validate()
