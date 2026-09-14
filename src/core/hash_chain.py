"""Cadena de hashes con deteccion de alteracion, reordenamiento y bifurcacion.

Reglas:
- Cada entrada incluye prev_event_hash (SHA-256 de la anterior).
- La genesis tiene prev_event_hash = "" y chain_position = "0".
- El event_hash se calcula sobre los bytes canonicos del evento sin el.
- Verificacion end-to-end valida encadenamiento, orden y unicidad.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Final

from .errors import EvidenceError
from .hashing import content_hash_bytes
from .jcs import canonicalize

GENESIS_PREV_HASH: Final[str] = ""


class ChainError(EvidenceError):
    """Error de integridad de la cadena."""


class ChainTamperError(ChainError):
    """Alteracion detectada en la cadena."""


class ChainReorderError(ChainError):
    """Reordenamiento detectado."""


class ChainForkError(ChainError):
    """Bifurcacion detectada."""


@dataclass(frozen=True)
class ChainEntry:
    event_id: str
    evidence_id: str
    event_type: str
    payload: dict[str, Any]
    occurred_at: str
    prev_event_hash: str
    chain_position: str
    event_hash: str = field(default="")

    def _payload_without_hash(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "evidence_id": self.evidence_id,
            "event_type": self.event_type,
            "payload": self.payload,
            "occurred_at": self.occurred_at,
            "prev_event_hash": self.prev_event_hash,
            "chain_position": self.chain_position,
        }

    def compute_hash(self) -> str:
        return content_hash_bytes(canonicalize(self._payload_without_hash())).hex()

    def to_dict(self) -> dict[str, Any]:
        d = self._payload_without_hash()
        d["event_hash"] = self.event_hash
        return d

    def canonical_bytes(self) -> bytes:
        return canonicalize(self.to_dict())


def genesis(
    event_id: str,
    evidence_id: str,
    event_type: str,
    payload: dict[str, Any],
    occurred_at: str,
) -> ChainEntry:
    entry = ChainEntry(
        event_id=event_id,
        evidence_id=evidence_id,
        event_type=event_type,
        payload=payload,
        occurred_at=occurred_at,
        prev_event_hash=GENESIS_PREV_HASH,
        chain_position="0",
    )
    return _with_hash(entry)


def append(
    previous: ChainEntry,
    event_id: str,
    event_type: str,
    payload: dict[str, Any],
    occurred_at: str,
) -> ChainEntry:
    entry = ChainEntry(
        event_id=event_id,
        evidence_id=previous.evidence_id,
        event_type=event_type,
        payload=payload,
        occurred_at=occurred_at,
        prev_event_hash=previous.event_hash,
        chain_position=str(int(previous.chain_position) + 1),
    )
    return _with_hash(entry)


def _with_hash(entry: ChainEntry) -> ChainEntry:
    computed = entry.compute_hash()
    return ChainEntry(
        event_id=entry.event_id,
        evidence_id=entry.evidence_id,
        event_type=entry.event_type,
        payload=entry.payload,
        occurred_at=entry.occurred_at,
        prev_event_hash=entry.prev_event_hash,
        chain_position=entry.chain_position,
        event_hash=computed,
    )


def verify_chain(entries: Iterable[ChainEntry]) -> None:
    """Verifica la cadena completa.

    Raises:
        ChainTamperError: hash de un evento no coincide.
        ChainReorderError: posiciones no consecutivas o prev_hash roto.
        ChainForkError: dos eventos comparten prev_event_hash.
    """
    seen_positions: set[str] = set()
    seen_prev_hashes: dict[str, str] = {}  # prev_hash -> event_id
    seen_event_hashes: set[str] = set()
    previous: ChainEntry | None = None

    for entry in entries:
        # Integridad del propio evento
        expected_hash = entry.compute_hash()
        if entry.event_hash != expected_hash:
            raise ChainTamperError(
                f"event_hash no coincide en {entry.event_id}"
            )

        # Unicidad de event_hash
        if entry.event_hash in seen_event_hashes:
            raise ChainTamperError(
                f"event_hash duplicado: {entry.event_id}"
            )
        seen_event_hashes.add(entry.event_hash)

        # Posicion
        if entry.chain_position in seen_positions:
            raise ChainReorderError(
                f"chain_position duplicado: {entry.chain_position}"
            )
        seen_positions.add(entry.chain_position)

        # Genesis
        if entry.chain_position == "0":
            if entry.prev_event_hash != GENESIS_PREV_HASH:
                raise ChainReorderError("Genesis con prev_event_hash no vacio")
            if previous is not None:
                raise ChainReorderError("Genesis no es el primer elemento")
        else:
            if previous is None:
                raise ChainReorderError(
                    f"Evento no genesis sin predecesor: {entry.event_id}"
                )
            if entry.prev_event_hash != previous.event_hash:
                raise ChainReorderError(
                    f"prev_event_hash no coincide en {entry.event_id}"
                )
            expected_position = str(int(previous.chain_position) + 1)
            if entry.chain_position != expected_position:
                raise ChainReorderError(
                    f"chain_position no consecutivo en {entry.event_id}"
                )

        # Fork: dos eventos con el mismo prev_hash
        if entry.prev_event_hash in seen_prev_hashes and entry.chain_position != "0":
            other = seen_prev_hashes[entry.prev_event_hash]
            if other != entry.event_id:
                raise ChainForkError(
                    f"Fork detectado: {entry.event_id} y {other} "
                    f"comparten prev_event_hash"
                )
        seen_prev_hashes[entry.prev_event_hash] = entry.event_id

        previous = entry
