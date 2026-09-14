"""Interfaz KMS. Las claves nunca salen del proveedor.

Regla de diseno:
- El codigo llamante nunca recibe material de clave.
- Toda operacion HMAC o de firma se delega al proveedor.
- Los tests usan LocalKMS; produccion usa AWSKMS, AzureKMS o VaultKMS.
"""

from __future__ import annotations

import hmac
from typing import Protocol, runtime_checkable

from .errors import EvidenceError


class KmsError(EvidenceError):
    """Error de KMS."""


@runtime_checkable
class KMSProvider(Protocol):
    """Contrato minimo de un proveedor KMS."""

    def hmac_sign(self, key_id: str, message: bytes) -> bytes:
        """Devuelve HMAC-SHA256(key_id, message). No expone la clave."""
        ...

    def hmac_verify(self, key_id: str, message: bytes, mac: bytes) -> bool:
        """Verifica HMAC en tiempo constante."""
        ...


class LocalKMS:
    """KMS en memoria. Solo para desarrollo y tests.

    No usar en produccion. Las claves viven en el proceso.
    """

    def __init__(self, keys: dict[str, bytes]) -> None:
        self._keys = {k: bytes(v) for k, v in keys.items()}

    def _get(self, key_id: str) -> bytes:
        key = self._keys.get(key_id)
        if key is None:
            raise KmsError(f"key_id desconocido: {key_id}")
        return key

    def hmac_sign(self, key_id: str, message: bytes) -> bytes:
        if not isinstance(message, (bytes, bytearray)):
            raise KmsError("message debe ser bytes")
        return hmac.new(self._get(key_id), bytes(message), "sha256").digest()

    def hmac_verify(self, key_id: str, message: bytes, mac: bytes) -> bool:
        try:
            expected = self.hmac_sign(key_id, message)
        except KmsError:
            return False
        return hmac.compare_digest(expected, bytes(mac))


class AWSKMS:
    """Stub de AWS KMS. Implementar antes de produccion.

    La interfaz esperada es GenerateMac/VerifyMac para HMAC y Sign/Verify
    para ECDSA. Las claves se referencian por ARN y nunca se exportan.
    """

    def __init__(self, region: str) -> None:
        self.region = region

    def hmac_sign(self, key_id: str, message: bytes) -> bytes:
        raise NotImplementedError("AWSKMS.hmac_sign pendiente de implementar")

    def hmac_verify(self, key_id: str, message: bytes, mac: bytes) -> bool:
        raise NotImplementedError("AWSKMS.hmac_verify pendiente de implementar")


class VaultKMS:
    """Stub de HashiCorp Vault. Implementar antes de produccion."""

    def __init__(self, addr: str, token: str) -> None:
        self.addr = addr
        self.token = token

    def hmac_sign(self, key_id: str, message: bytes) -> bytes:
        raise NotImplementedError("VaultKMS.hmac_sign pendiente de implementar")

    def hmac_verify(self, key_id: str, message: bytes, mac: bytes) -> bool:
        raise NotImplementedError("VaultKMS.hmac_verify pendiente de implementar")
