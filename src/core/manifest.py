"""Construccion y validacion del manifiesto v1.

Valida contra schemas/manifest-v1.schema.json con jsonschema.
Adicionalmente aplica reglas internas (chain_position coherente, etc.).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final

import jsonschema

from .errors import ManifestError, ManifestValidationError
from .hashing import COMMITMENT_ALGORITHM, CONTENT_HASH_ALGORITHM
from .jcs import canonicalize

MANIFEST_VERSION: Final[str] = "1.0"
MANIFEST_SCHEMA_URN: Final[str] = "urn:evidence-integrity:manifest:v1"

_SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schemas" / "manifest-v1.schema.json"
_SCHEMA_CACHE: dict[str, Any] | None = None


def _schema() -> dict[str, Any]:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        with _SCHEMA_PATH.open(encoding="utf-8") as f:
            _SCHEMA_CACHE = json.load(f)
    return _SCHEMA_CACHE


@dataclass(frozen=True)
class Content:
    content_hash: str
    size_bytes: str
    mime_type: str


@dataclass(frozen=True)
class Commitment:
    context_id: str
    private_commitment: str
    kms_key_id: str


@dataclass(frozen=True)
class Chain:
    previous_manifest_hash: str
    chain_position: str


@dataclass(frozen=True)
class Manifest:
    evidence_id: str
    created_at: datetime
    content: Content
    commitment: Commitment
    chain: Chain
    original_included: bool = False

    def to_payload(self) -> dict[str, Any]:
        return {
            "$schema": MANIFEST_SCHEMA_URN,
            "manifest_version": MANIFEST_VERSION,
            "evidence_id": self.evidence_id,
            "created_at": _iso8601(self.created_at),
            "content": {
                "hash_algorithm": CONTENT_HASH_ALGORITHM,
                "content_hash": self.content.content_hash,
                "size_bytes": self.content.size_bytes,
                "mime_type": self.content.mime_type,
            },
            "commitment": {
                "algorithm": COMMITMENT_ALGORITHM,
                "context_id": self.commitment.context_id,
                "private_commitment": self.commitment.private_commitment,
                "kms_key_id": self.commitment.kms_key_id,
            },
            "chain": {
                "previous_manifest_hash": self.chain.previous_manifest_hash,
                "chain_position": self.chain.chain_position,
            },
            "original_included": self.original_included,
        }

    def canonical_bytes(self) -> bytes:
        return canonicalize(self.to_payload())

    def validate(self) -> None:
        payload = self.to_payload()
        try:
            jsonschema.validate(payload, _schema())
        except jsonschema.ValidationError as exc:
            raise ManifestValidationError(
                f"Esquema: {exc.message} en {list(exc.path)}"
            ) from exc
        _validate_internal_rules(self)


def _iso8601(dt: datetime) -> str:
    if dt.tzinfo is None:
        raise ManifestError("created_at debe tener zona horaria")
    utc = dt.astimezone(timezone.utc)
    return utc.strftime("%Y-%m-%dT%H:%M:%S.") + f"{utc.microsecond // 1000:03d}Z"


def _validate_internal_rules(m: Manifest) -> None:
    if m.chain.chain_position == "0":
        if m.chain.previous_manifest_hash:
            raise ManifestValidationError(
                "chain_position=0 no debe declarar previous_manifest_hash"
            )
    else:
        if len(m.chain.previous_manifest_hash) != 64:
            raise ManifestValidationError(
                "previous_manifest_hash debe ser hex de 64 caracteres"
            )
