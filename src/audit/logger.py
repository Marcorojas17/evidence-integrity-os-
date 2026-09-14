"""Log de auditoría con encadenamiento y firma por evento.

Reglas:
- JSONL: una línea por evento.
- Cada evento incluye prev_event_hash (SHA-256 del anterior).
- event_hash = SHA-256(JCS(evento sin event_hash ni signature)).
- signature = JWS detached RFC 7797 sobre JCS(evento sin event_hash ni signature).
- Genesis con prev_event_hash="" y event_type="genesis".
- Al leer, se reconstruye el listado; verificar la cadena es responsabilidad
  de src/audit/integrity.py.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Final

from cryptography.hazmat.primitives.asymmetric.ec import (
    EllipticCurvePrivateKey,
)

from src.core.hash_chain import GENESIS_PREV_HASH
from src.core.hashing import content_hash_bytes
from src.core.jcs import canonicalize
from src.core.jws import sign_detached

from .errors import AuditError

GENESIS_EVENT_TYPE: Final[str] = "genesis"


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    occurred_at: str
    event_type: str
    payload: dict[str, Any]
    prev_event_hash: str
    event_hash: str
    signature: str  # JWS completo serializado a JSON

    def _payload_without_integrity(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "occurred_at": self.occurred_at,
            "event_type": self.event_type,
            "payload": self.payload,
            "prev_event_hash": self.prev_event_hash,
        }

    def compute_hash(self) -> str:
        return content_hash_bytes(
            canonicalize(self._payload_without_integrity())
        ).hex()

    def to_dict(self) -> dict[str, Any]:
        d = self._payload_without_integrity()
        d["event_hash"] = self.event_hash
        d["signature"] = self.signature
        return d

    def canonical_bytes(self) -> bytes:
        return canonicalize(self.to_dict())


def genesis_event(
    *,
    event_id: str,
    occurred_at: str,
    payload: dict[str, Any],
    signing_key: EllipticCurvePrivateKey,
    signing_kid: str,
    signing_x5c: list[str],
) -> AuditEvent:
    return _make_event(
        event_id=event_id,
        occurred_at=occurred_at,
        event_type=GENESIS_EVENT_TYPE,
        payload=payload,
        prev_event_hash=GENESIS_PREV_HASH,
        signing_key=signing_key,
        signing_kid=signing_kid,
        signing_x5c=signing_x5c,
    )


def append_event(
    previous: AuditEvent,
    *,
    event_id: str,
    occurred_at: str,
    event_type: str,
    payload: dict[str, Any],
    signing_key: EllipticCurvePrivateKey,
    signing_kid: str,
    signing_x5c: list[str],
) -> AuditEvent:
    if not previous.event_hash:
        raise AuditError("Evento anterior sin event_hash")
    if event_type == GENESIS_EVENT_TYPE:
        raise AuditError("genesis solo puede ser el primer evento")
    return _make_event(
        event_id=event_id,
        occurred_at=occurred_at,
        event_type=event_type,
        payload=payload,
        prev_event_hash=previous.event_hash,
        signing_key=signing_key,
        signing_kid=signing_kid,
        signing_x5c=signing_x5c,
    )


def new_event_id() -> str:
    return f"evt_{uuid.uuid4().hex[:16]}"


def _make_event(
    *,
    event_id: str,
    occurred_at: str,
    event_type: str,
    payload: dict[str, Any],
    prev_event_hash: str,
    signing_key: EllipticCurvePrivateKey,
    signing_kid: str,
    signing_x5c: list[str],
) -> AuditEvent:
    if not event_id:
        raise AuditError("event_id obligatorio")
    if not occurred_at:
        raise AuditError("occurred_at obligatorio")

    skeleton = AuditEvent(
        event_id=event_id,
        occurred_at=occurred_at,
        event_type=event_type,
        payload=payload,
        prev_event_hash=prev_event_hash,
        event_hash="",
        signature="",
    )
    payload_bytes = canonicalize(skeleton._payload_without_integrity())
    event_hash = content_hash_bytes(payload_bytes).hex()

    jws = sign_detached(
        payload_bytes=payload_bytes,
        private_key=signing_key,
        kid=signing_kid,
        x5c=signing_x5c,
    )

    return AuditEvent(
        event_id=event_id,
        occurred_at=occurred_at,
        event_type=event_type,
        payload=payload,
        prev_event_hash=prev_event_hash,
        event_hash=event_hash,
        signature=json.dumps(jws, separators=(",", ":")),
    )


def write_event(path: str | Path, event: AuditEvent) -> None:
    """Añade una línea JSONL al archivo de auditoría."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    line = event.canonical_bytes() + b"\n"
    with p.open("ab") as f:
        f.write(line)


def read_events(path: str | Path) -> list[AuditEvent]:
    """Lee el archivo JSONL y reconstruye los eventos."""
    p = Path(path)
    if not p.is_file():
        raise AuditError(f"Archivo de auditoría no encontrado: {p}")
    events: list[AuditEvent] = []
    with p.open("rb") as f:
        for lineno, raw in enumerate(f, start=1):
            raw = raw.rstrip(b"\n")
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise AuditError(f"Línea {lineno} no es JSON válido") from exc
            events.append(
                AuditEvent(
                    event_id=obj["event_id"],
                    occurred_at=obj["occurred_at"],
                    event_type=obj["event_type"],
                    payload=obj["payload"],
                    prev_event_hash=obj["prev_event_hash"],
                    event_hash=obj["event_hash"],
                    signature=obj["signature"],
                )
            )
    return events


def canonical_log_bytes(events: Iterable[AuditEvent]) -> bytes:
    """Bytes canónicos del log completo (una línea JCS por evento)."""
    return b"\n".join(e.canonical_bytes() for e in events) + b"\n"
