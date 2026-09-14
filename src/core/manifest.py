"""Construccion y validacion del manifiesto v1.

El manifiesto es el payload canonico firmado. No contiene firma, token
de tiempo ni anclaje: esas pruebas viven fuera del alcance firmado.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .errors import ManifestError, ManifestValidationError
from .hashing import CONTENT_HASH_ALGORITHM, COMMITMENT_ALGORITHM
from .jcs import canonicalize

MANIFEST_VERSION: str = "1.0"
MANIFEST_SCHEMA_URN: str = "urn:evidence-integrity:manifest:v1"


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
        """Convierte el manifiesto al dict canonico."""
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
        """Devuelve los bytes canonicos RFC 8785 del manifiesto."""
        return canonicalize(self.to_payload())

    def validate(self) -> None:
        """Valida el manifiesto contra el esquema y reglas internas."""
        _validate_manifest(self)


def _iso8601(dt: datetime) -> str:
    if dt.tzinfo is None:
        raise ManifestError("created_at debe tener zona horaria")
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + \
        f"{dt.microsecond // 1000:03d}Z"


def _validate_manifest(m: Manifest) -> None:
    if not m.evidence_id or not m.evidence_id.startswith("ev_"):
        raise ManifestValidationError(
            "evidence_id debe comenzar con 'ev_'"
        )
    if len(m.content.content_hash) != 64:
        raise ManifestValidationError(
            "content_hash debe ser hex de 64 caracteres (SHA-256)"
        )
    if len(m.commitment.private_commitment) != 64:
        raise ManifestValidationError(
            "private_commitment debe ser hex de 64 caracteres (HMAC-SHA256)"
        )
    if not m.content.size_bytes.isdigit():
        raise ManifestValidationError(
            "size_bytes debe ser string numerico"
        )
    if not m.chain.chain_position.isdigit():
        raise ManifestValidationError(
            "chain_position debe ser string numerico"
        )
    if m.chain.chain_position != "0":
        prev = m.chain.previous_manifest_hash
        if len(prev) != 64:
            raise ManifestValidationError(
                "previous_manifest_hash debe ser hex de 64 caracteres"
            )
    elif m.chain.previous_manifest_hash:
        raise ManifestValidationError(
            "chain_position=0 no debe declarar previous_manifest_hash"
        )
