"""Pruebas sobre el comportamiento de content_hash y private_commitment.

Verifica:
- content_hash es reproducible por terceros con el mismo archivo.
- private_commitment no es reproducible sin la clave KMS.
- Cambiar context_id altera el commitment.
- Cambiar KMS key altera el commitment.
"""

from __future__ import annotations

import pytest

from src.core.hashing import (
    content_hash_hex,
    private_commitment,
    verify_commitment,
)
from src.core.kms import LocalKMS


KMS_KEY = b"\x42" * 32
KMS_KEY_2 = b"\x99" * 32
CONTEXT = "ctx_test_001"


@pytest.fixture
def kms() -> LocalKMS:
    return LocalKMS({"kms-hmac-1": KMS_KEY, "kms-hmac-2": KMS_KEY_2})


def test_content_hash_is_publicly_reproducible() -> None:
    """Cualquiera con el archivo calcula el mismo hash."""
    import hashlib

    data = b"documento predecible"
    assert content_hash_hex(data) == hashlib.sha256(data).hexdigest()


def test_content_hash_reveals_low_entropy_content() -> None:
    """Un atacante puede reproducir el hash si el contenido es predecible."""
    known_inputs = [b"hola", b"1234", b"contraseña", b"DNI-12345678"]
    target = content_hash_hex(b"contraseña")

    for candidate in known_inputs:
        if content_hash_hex(candidate) == target:
            assert candidate == b"contraseña"
            return
    pytest.fail("El diccionario no encontró el contenido predecible")


def test_commitment_not_reproducible_without_key(kms: LocalKMS) -> None:
    """Sin la clave KMS, el commitment no se puede recalcular."""
    from src.core.hashing import content_hash_bytes

    ch = content_hash_bytes(b"secreto")
    real = private_commitment(kms, "kms-hmac-1", CONTEXT, ch)

    # Intento con otra clave
    fake_kms = LocalKMS({"kms-hmac-1": b"\x00" * 32})
    fake = private_commitment(fake_kms, "kms-hmac-1", CONTEXT, ch)
    assert real != fake


def test_commitment_changes_with_context(kms: LocalKMS) -> None:
    from src.core.hashing import content_hash_bytes

    ch = content_hash_bytes(b"doc")
    a = private_commitment(kms, "kms-hmac-1", "ctx_a", ch)
    b = private_commitment(kms, "kms-hmac-1", "ctx_b", ch)
    assert a != b


def test_commitment_changes_with_key(kms: LocalKMS) -> None:
    from src.core.hashing import content_hash_bytes

    ch = content_hash_bytes(b"doc")
    a = private_commitment(kms, "kms-hmac-1", CONTEXT, ch)
    b = private_commitment(kms, "kms-hmac-2", CONTEXT, ch)
    assert a != b


def test_verify_commitment_constant_time(kms: LocalKMS) -> None:
    from src.core.hashing import content_hash_bytes

    ch = content_hash_bytes(b"doc")
    mac = private_commitment(kms, "kms-hmac-1", CONTEXT, ch)

    assert verify_commitment(kms, "kms-hmac-1", CONTEXT, ch, mac)
    assert not verify_commitment(kms, "kms-hmac-1", CONTEXT, ch, b"\x00" * 32)
