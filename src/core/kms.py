"""Interfaz KMS. Las claves nunca salen del proveedor.

Proveedores:
- LocalKMS: en memoria, solo tests y desarrollo.
- AWSKMS: AWS Key Management Service con GenerateMac/VerifyMac.
- AzureKMS: Azure Key Vault (pendiente).
- VaultKMS: HashiCorp Vault (pendiente).

Regla de diseño:
- El código llamante nunca recibe material de clave.
- Toda operación HMAC o de firma se delega al proveedor.
"""

from __future__ import annotations

import hmac
from typing import Any, Protocol, runtime_checkable

from .errors import EvidenceError

AWS_HMAC_ALGORITHM = "HMAC_SHA_256"
AWS_MAC_LENGTH_BYTES = 32


class KmsError(EvidenceError):
    """Error de KMS."""


@runtime_checkable
class KMSProvider(Protocol):
    """Contrato mínimo de un proveedor KMS."""

    def hmac_sign(self, key_id: str, message: bytes) -> bytes:
        """Devuelve HMAC-SHA256(key_id, message). No expone la clave."""
        ...

    def hmac_verify(self, key_id: str, message: bytes, mac: bytes) -> bool:
        """Verifica HMAC en tiempo constante."""
        ...


class LocalKMS:
    """KMS en memoria. Solo para desarrollo y tests.

    No usar en producción. Las claves viven en el proceso.
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
    """Implementación real usando AWS KMS GenerateMac/VerifyMac.

    Requisitos:
    - boto3 instalado.
    - Clave HMAC creada en KMS con KeySpec=HMAC_256.
    - IAM con permisos kms:GenerateMac y kms:VerifyMac.
    - Región configurada.
    """

    def __init__(
        self,
        region: str,
        *,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        aws_session_token: str | None = None,
        endpoint_url: str | None = None,
    ) -> None:
        try:
            import boto3
        except ImportError as exc:
            raise KmsError(
                "boto3 no instalado. Ejecutar: pip install boto3"
            ) from exc

        self._region = region
        self._client = boto3.client(
            "kms",
            region_name=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            endpoint_url=endpoint_url,
        )

    def hmac_sign(self, key_id: str, message: bytes) -> bytes:
        if not isinstance(message, (bytes, bytearray)):
            raise KmsError("message debe ser bytes")
        try:
            response: dict[str, Any] = self._client.generate_mac(
                KeyId=key_id,
                MacAlgorithm=AWS_HMAC_ALGORITHM,
                Message=bytes(message),
            )
        except Exception as exc:
            raise KmsError(f"AWS generate_mac falló: {exc}") from exc

        mac = response.get("Mac")
        if not isinstance(mac, (bytes, bytearray)):
            raise KmsError("Respuesta de KMS sin campo Mac")
        if len(mac) != AWS_MAC_LENGTH_BYTES:
            raise KmsError(
                f"Longitud de MAC inesperada: {len(mac)} bytes"
            )
        return bytes(mac)

    def hmac_verify(self, key_id: str, message: bytes, mac: bytes) -> bool:
        if not isinstance(message, (bytes, bytearray)):
            raise KmsError("message debe ser bytes")
        if not isinstance(mac, (bytes, bytearray)):
            raise KmsError("mac debe ser bytes")
        try:
            response: dict[str, Any] = self._client.verify_mac(
                KeyId=key_id,
                MacAlgorithm=AWS_HMAC_ALGORITHM,
                Message=bytes(message),
                Mac=bytes(mac),
            )
        except self._client.exceptions.KMSInvalidMacException:
            return False
        except Exception as exc:
            raise KmsError(f"AWS verify_mac falló: {exc}") from exc

        return bool(response.get("MacValid", False))


class AzureKMS:
    """Stub de Azure Key Vault. Implementar antes de producción.

    La interfaz esperada usa CryptographyClient con algoritmos HMAC-SHA256.
    """

    def __init__(self, vault_url: str) -> None:
        self.vault_url = vault_url

    def hmac_sign(self, key_id: str, message: bytes) -> bytes:
        raise NotImplementedError("AzureKMS.hmac_sign pendiente")

    def hmac_verify(self, key_id: str, message: bytes, mac: bytes) -> bool:
        raise NotImplementedError("AzureKMS.hmac_verify pendiente")


class VaultKMS:
    """Stub de HashiCorp Vault. Implementar antes de producción."""

    def __init__(self, addr: str, token: str) -> None:
        self.addr = addr
        self.token = token

    def hmac_sign(self, key_id: str, message: bytes) -> bytes:
        raise NotImplementedError("VaultKMS.hmac_sign pendiente")

    def hmac_verify(self, key_id: str, message: bytes, mac: bytes) -> bool:
        raise NotImplementedError("VaultKMS.hmac_verify pendiente")


def build_kms_from_env(env: dict[str, str]) -> KMSProvider:
    """Construye el KMS adecuado según variables de entorno.

    KMS_BACKEND=local | aws | azure | vault
    """
    backend = env.get("KMS_BACKEND", "local").lower()

    if backend == "local":
        keys_raw = env.get("KMS_LOCAL_KEYS", "")
        keys: dict[str, bytes] = {}
        for pair in keys_raw.split(","):
            pair = pair.strip()
            if not pair or ":" not in pair:
                continue
            key_id, hex_key = pair.split(":", 1)
            keys[key_id.strip()] = bytes.fromhex(hex_key.strip())
        if not keys:
            raise KmsError(
                "KMS_BACKEND=local sin KMS_LOCAL_KEYS configurado"
            )
        return LocalKMS(keys)

    if backend == "aws":
        region = env.get("KMS_AWS_REGION", "")
        if not region:
            raise KmsError("KMS_AWS_REGION no configurado")
        return AWSKMS(
            region=region,
            aws_access_key_id=env.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=env.get("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=env.get("AWS_SESSION_TOKEN"),
        )

    if backend == "azure":
        vault_url = env.get("KMS_AZURE_VAULT_URL", "")
        if not vault_url:
            raise KmsError("KMS_AZURE_VAULT_URL no configurado")
        return AzureKMS(vault_url)

    if backend == "vault":
        addr = env.get("KMS_VAULT_ADDR", "")
        token = env.get("KMS_VAULT_TOKEN", "")
        if not addr or not token:
            raise KmsError("KMS_VAULT_ADDR y KMS_VAULT_TOKEN requeridos")
        return VaultKMS(addr, token)

    raise KmsError(f"KMS_BACKEND desconocido: {backend}")
