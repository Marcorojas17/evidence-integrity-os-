"""Anclaje externo de cierres del log de auditoría.

El anclaje es lo que hace que un cierre sea verificable sin depender
del propio sistema. Proveedores soportados:

- LocalFilesystemAnchor: directorio local (solo desarrollo/tests)
- S3ObjectLockAnchor: AWS S3 con Object Lock (stub)
- AzureImmutableBlobAnchor: Azure Immutable Blob (stub)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Final, Protocol, runtime_checkable

from .errors import AuditAnchorError

ANCHOR_FILENAME_TEMPLATE: Final[str] = "close_{close_id}.bin"


@dataclass(frozen=True)
class AnchorRecord:
    close_id: str
    close_hash: str
    anchored_at: str
    location: str


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
    """Stub de AWS S3 con Object Lock. Implementar antes de producción."""

    def __init__(self, bucket: str, prefix: str = "audit-closes/") -> None:
        self.bucket = bucket
        self.prefix = prefix

    def put(self, close_id: str, close_bytes: bytes) -> AnchorRecord:
        raise NotImplementedError("S3ObjectLockAnchor.put pendiente")

    def get(self, close_id: str) -> AnchorRecord | None:
        raise NotImplementedError("S3ObjectLockAnchor.get pendiente")

    def read(self, close_id: str) -> bytes:
        raise NotImplementedError("S3ObjectLockAnchor.read pendiente")


class AzureImmutableBlobAnchor:
    """Stub de Azure Immutable Blob. Implementar antes de producción."""

    def __init__(self, container_url: str, prefix: str = "audit-closes/") -> None:
        self.container_url = container_url
        self.prefix = prefix

    def put(self, close_id: str, close_bytes: bytes) -> AnchorRecord:
        raise NotImplementedError("AzureImmutableBlobAnchor.put pendiente")

    def get(self, close_id: str) -> AnchorRecord | None:
        raise NotImplementedError("AzureImmutableBlobAnchor.get pendiente")

    def read(self, close_id: str) -> bytes:
        raise NotImplementedError("AzureImmutableBlobAnchor.read pendiente")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
