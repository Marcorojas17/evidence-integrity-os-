"""Hashing SHA-256 y compromiso HMAC con comparacion constante.

Reglas:
- content_hash: SHA-256 del archivo. Interoperable, verificable por terceros.
- private_commitment: HMAC-SHA256(KMS_key, context_id || content_hash).
- Comparacion siempre con hmac.compare_digest (constant-time).
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Final

from .errors import HashingError

CHUNK_SIZE: Final[int] = 1024 * 1024  # 1 MiB

CONTENT_HASH_ALGORITHM: Final[str] = "sha256"
COMMITMENT_ALGORITHM: Final[str] = "hmac-sha256"


def content_hash_bytes(data: bytes) -> bytes:
    """Calcula SHA-256 de un bloque de bytes."""
    if not isinstance(data, (bytes, bytearray)):
        raise HashingError("content_hash_bytes espera bytes")
    return hashlib.sha256(data).digest()


def content_hash_hex(data: bytes) -> str:
    """Calcula SHA-256 y devuelve hex en minusculas."""
    return content_hash_bytes(data).hex()


def content_hash_file(path: str) -> str:
    """Calcula SHA-256 de un archivo por chunks, sin cargarlo en memoria."""
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                h.update(chunk)
    except OSError as exc:
        raise HashingError(f"No se pudo leer el archivo: {path}") from exc
    return h.hexdigest()


def private_commitment(
    kms_key: bytes,
    context_id: str,
    content_hash: bytes,
) -> bytes:
    """HMAC-SHA256 del content_hash usando una clave KMS.

    Args:
        kms_key: clave secreta obtenida del KMS. Nunca viaja al cliente.
        context_id: identificador publico de contexto (no secreto).
        content_hash: digest binario SHA-256 del archivo.

    Returns:
        Digest binario HMAC-SHA256.
    """
    if not isinstance(kms_key, (bytes, bytearray)) or not kms_key:
        raise HashingError("kms_key debe ser bytes no vacios")
    if not isinstance(context_id, str) or not context_id:
        raise HashingError("context_id debe ser string no vacio")
    if not isinstance(content_hash, (bytes, bytearray)):
        raise HashingError("content_hash debe ser bytes")

    msg = context_id.encode("utf-8") + bytes(content_hash)
    return hmac.new(kms_key, msg, hashlib.sha256).digest()


def constant_time_eq(a: bytes, b: bytes) -> bool:
    """Comparacion en tiempo constante."""
    if not isinstance(a, (bytes, bytearray)):
        raise HashingError("a debe ser bytes")
    if not isinstance(b, (bytes, bytearray)):
        raise HashingError("b debe ser bytes")
    return hmac.compare_digest(bytes(a), bytes(b))
