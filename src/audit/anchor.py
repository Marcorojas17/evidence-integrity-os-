"""Anclaje externo de cierres del log de auditoría.

Proveedores:
- LocalFilesystemAnchor: directorio local, solo dev/tests.
- S3ObjectLockAnchor: AWS S3 con Object Lock en modo COMPLIANCE.
- AzureImmutableBlobAnchor: Azure Blob con immutability policy (stub).

Regla:
- El anclaje es lo que hace que un cierre sea verificable sin depender
  del propio sistema.
- put() es idempotente: si el close_id ya existe con contenido distinto,
  falla. Esto protege contra sustituciones.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Final, Protocol, runtime_checkable

from .errors import AuditAnchorError

ANCHOR_FILENAME_TEMPLATE: Final[str] = "close_{close_id}.bin"
DEFAULT_RETENTION_DAYS: Final[int] = 3650  # 10 años


@dataclass(frozen=True)
class AnchorRecord:
    close_id: str
    close_hash: str
    anchored_at: str
    location: str
    retention_until: str | None = None


@runtime_checkable
class AnchorProvider(Protocol):
    """Contrato de un proveedor de anclaje."""

    def put(self, close_id: str, close_bytes: bytes) -> AnchorRecord: ...
    def get(self, close_id: str) -> AnchorRecord | None: ...
    def read(self, close_id: str) -> bytes: ...


class LocalFilesystemAnchor:
    """Anclaje en disco local. Solo para desarrollo y pruebas."""

    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, close_id: str) -> Path:
        if not close_id or "/" in close_id or "\\" in close_id:
            raise AuditAnchorError(f"close_id inválido: {close_id!r}")
        return self.base_dir / ANCHOR_FILENAME_TEMPLATE.format(close_id=close_id)

    def put(self, close_id: str, close_bytes: bytes) -> AnchorRecord:
        if not isinstance(close_bytes, (bytes, bytearray)):
            raise AuditAnchorError("close_bytes debe ser bytes")
        path = self._path(close_id)
        if path.exists():
            existing = path.read_bytes()
            if existing != bytes(close_bytes):
                raise AuditAnchorError(
                    f"close_id ya existe con contenido distinto: {close_id}"
                )
        else:
            path.write_bytes(bytes(close_bytes))
        from src.core.hashing import content_hash_bytes

        return AnchorRecord(
            close_id=close_id,
            close_hash=content_hash_bytes(bytes(close_bytes)).hex(),
            anchored_at=_now_iso(),
            location=str(path),
        )

    def get(self, close_id: str) -> AnchorRecord | None:
        path = self._path(close_id)
        if not path.is_file():
            return None
        from src.core.hashing import content_hash_bytes

        data = path.read_bytes()
        return AnchorRecord(
            close_id=close_id,
            close_hash=content_hash_bytes(data).hex(),
            anchored_at=_now_iso(),
            location=str(path),
        )

    def read(self, close_id: str) -> bytes:
        path = self._path(close_id)
        if not path.is_file():
            raise AuditAnchorError(f"Anclaje no encontrado: {close_id}")
        return path.read_bytes()


class S3ObjectLockAnchor:
    """Implementación real con AWS S3 + Object Lock (COMPLIANCE).

    Requisitos:
    - Bucket con Object Lock habilitado al momento de su creación.
    - Versioning habilitado.
    - IAM con s3:PutObject, s3:GetObject, s3:GetObjectRetention.
    - Modo COMPLIANCE si el objeto no debe poder borrarse ni por el
      propietario de la cuenta antes de la fecha de retención.

    Nota operativa:
    - S3 Object Lock no puede habilitarse retroactivamente. El bucket
      debe crearse con --object-lock-enabled-for-bucket.
    """

    def __init__(
        self,
        bucket: str,
        *,
        prefix: str = "audit-closes/",
        region: str = "us-east-1",
        retention_days: int = DEFAULT_RETENTION_DAYS,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        aws_session_token: str | None = None,
        endpoint_url: str | None = None,
    ) -> None:
        try:
            import boto3
        except ImportError as exc:
            raise AuditAnchorError(
                "boto3 no instalado. Ejecutar: pip install boto3"
            ) from exc

        if retention_days < 1:
            raise AuditAnchorError("retention_days debe ser >= 1")

        self.bucket = bucket
        self.prefix = prefix.rstrip("/") + "/"
        self.region = region
        self.retention_days = retention_days
        self._client = boto3.client(
            "s3",
            region_name=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token,
            endpoint_url=endpoint_url,
        )

    def _key(self, close_id: str) -> str:
        if not close_id or "/" in close_id or "\\" in close_id:
            raise AuditAnchorError(f"close_id inválido: {close_id!r}")
        return f"{self.prefix}{ANCHOR_FILENAME_TEMPLATE.format(close_id=close_id)}"

    def put(self, close_id: str, close_bytes: bytes) -> AnchorRecord:
        if not isinstance(close_bytes, (bytes, bytearray)):
            raise AuditAnchorError("close_bytes debe ser bytes")
        from src.core.hashing import content_hash_bytes

        key = self._key(close_id)
        content_hash = content_hash_bytes(bytes(close_bytes)).hex()

        existing = self.get(close_id)
        if existing is not None:
            if existing.close_hash != content_hash:
                raise AuditAnchorError(
                    f"close_id ya existe con contenido distinto: {close_id}"
                )
            return existing

        retention_until = _future_iso(self.retention_days)

        try:
            self._client.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=bytes(close_bytes),
                ObjectLockMode="COMPLIANCE",
                ObjectLockRetainUntilDate=retention_until,
                ContentType="application/octet-stream",
                Metadata={
                    "close-id": close_id,
                    "close-hash": content_hash,
                },
            )
        except Exception as exc:
            raise AuditAnchorError(f"S3 put_object falló: {exc}") from exc

        return AnchorRecord(
            close_id=close_id,
            close_hash=content_hash,
            anchored_at=_now_iso(),
            location=f"s3://{self.bucket}/{key}",
            retention_until=retention_until,
        )

    def get(self, close_id: str) -> AnchorRecord | None:
        key = self._key(close_id)
        try:
            head = self._client.head_object(Bucket=self.bucket, Key=key)
        except self._client.exceptions.NoSuchKey:
            return None
        except Exception as exc:
            # S3 devuelve 404 como ClientError sin NoSuchKey en algunos casos
            if "404" in str(exc) or "Not Found" in str(exc):
                return None
            raise AuditAnchorError(f"S3 head_object falló: {exc}") from exc

        metadata = head.get("Metadata", {}) or {}
        close_hash = metadata.get("close-hash", "")
        retention_until = None
        if head.get("ObjectLockRetainUntilDate"):
            retention_until = head["ObjectLockRetainUntilDate"].isoformat()

        return AnchorRecord(
            close_id=close_id,
            close_hash=close_hash,
            anchored_at=_now_iso(),
            location=f"s3://{self.bucket}/{key}",
            retention_until=retention_until,
        )

    def read(self, close_id: str) -> bytes:
        key = self._key(close_id)
        try:
            response = self._client.get_object(Bucket=self.bucket, Key=key)
            return response["Body"].read()
        except Exception as exc:
            raise AuditAnchorError(f"S3 get_object falló: {exc}") from exc


class AzureImmutableBlobAnchor:
    """Stub de Azure Blob con immutability policy. Implementar antes de producción."""

    def __init__(self, container_url: str, prefix: str = "audit-closes/") -> None:
        self.container_url = container_url
        self.prefix = prefix

    def put(self, close_id: str, close_bytes: bytes) -> AnchorRecord:
        raise NotImplementedError("AzureImmutableBlobAnchor.put pendiente")

    def get(self, close_id: str) -> AnchorRecord | None:
        raise NotImplementedError("AzureImmutableBlobAnchor.get pendiente")

    def read(self, close_id: str) -> bytes:
        raise NotImplementedError("AzureImmutableBlobAnchor.read pendiente")


def build_anchor_from_env(env: dict[str, str]) -> AnchorProvider:
    """Construye el anclaje adecuado según variables de entorno.

    ANCHOR_BACKEND=local | s3 | azure
    """
    backend = env.get("ANCHOR_BACKEND", "local").lower()

    if backend == "local":
        path = env.get("ANCHOR_LOCAL_PATH", "./anchors")
        return LocalFilesystemAnchor(path)

    if backend == "s3":
        bucket = env.get("ANCHOR_S3_BUCKET", "")
        region = env.get("ANCHOR_S3_REGION", env.get("KMS_AWS_REGION", "us-east-1"))
        if not bucket:
            raise AuditAnchorError("ANCHOR_S3_BUCKET no configurado")
        retention_days = int(env.get("ANCHOR_S3_RETENTION_DAYS", str(DEFAULT_RETENTION_DAYS)))
        return S3ObjectLockAnchor(
            bucket=bucket,
            region=region,
            retention_days=retention_days,
            aws_access_key_id=env.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=env.get("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=env.get("AWS_SESSION_TOKEN"),
        )

    if backend == "azure":
        url = env.get("ANCHOR_AZURE_CONTAINER_URL", "")
        if not url:
            raise AuditAnchorError("ANCHOR_AZURE_CONTAINER_URL no configurado")
        return AzureImmutableBlobAnchor(url)

    raise AuditAnchorError(f"ANCHOR_BACKEND desconocido: {backend}")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _future_iso(days: int) -> str:
    from datetime import timedelta

    return (
        datetime.now(timezone.utc) + timedelta(days=days)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
