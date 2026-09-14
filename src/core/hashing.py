"""Hashing SHA-256 y compromiso HMAC delegado a KMS.

Reglas:
- content_hash: SHA-256 del archivo. Interoperable.
- private_commitment: HMAC-SHA256 delegado al KMS. Nunca se recibe clave.
- Comparacion siempre con hmac.compare_digest (constant-time).
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Final

from .errors import HashingError
from .kms import KMSProvider

CHUNK_SIZE: Final[int] = 1024 * 1024

CONTENT_HASH_ALGORITHM: Final[str] = "sha256"
COMMITMENT_ALGORITHM: Final[str] = "hmac-sha256"


def content_hash_bytes(data: bytes) -> bytes:
    if not isinstance(data, (bytes, bytearray)):
        raise HashingError("content_hash_bytes espera bytes")
    return hashlib.sha256(data).digest()


def content_hash_hex(data: bytes) -> str:
    return content_hash_bytes(data).hex()


def content_hash_file(path: str) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                h.update(chunk)
    except OSError as exc:
        raise HashingError(f"No se pudo leer el archivo: {path}") from exc
    return h.hexdigest()


def private_commitment(
    kms: KMSProvider,
    key_id: str,
    context_id: str,
    content_hash: bytes,
) -> bytes:
    """HMAC-SHA256 delegado al KMS.

    La clave nunca se recibe en esta funcion.
    """
    if not isinstance(context_id, str) or not context_id:
        raise HashingError("context_id debe ser string no vacio")
    if not isinstance(content_hash, (bytes, bytearray)):
        raise HashingError("content_hash debe ser bytes")

    message = context_id.encode("utf-8") + bytes(content_hash)
    return kms.hmac_sign(key_id, message)


def verify_commitment(
    kms: KMSProvider,
    key_id: str,
    context_id: str,
    content_hash: bytes,
    expected: bytes,
) -> bool:
    message = context_id.encode("utf-8") + bytes(content_hash)
    return kms.hmac_verify(key_id, message, expected)


def constant_time_eq(a: bytes, b: bytes) -> bool:
    if not isinstance(a, (bytes, bytearray)):
        raise HashingError("a debe ser bytes")
    if not isinstance(b, (bytes, bytearray)):
        raise HashingError("b debe ser bytes")
    return hmac.compare_digest(bytes(a), bytes(b))
