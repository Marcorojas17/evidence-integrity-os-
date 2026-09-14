"""Cierre del log, verificación de cadena y de anclajes.

Un cierre (AuditClose) es un snapshot firmado del log completo hasta
un evento N. El cierre se ancla externamente y se puede verificar sin
depender del sistema original.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final

from cryptography.hazmat.primitives.asymmetric.ec import (
    EllipticCurvePrivateKey,
)

from src.core.hashing import content_hash_bytes
from src.core.jcs import canonicalize
from src.core.jws import sign_detached, verify_detached

from .anchor import AnchorProvider
from .errors import (
    AuditChainError,
    AuditCloseError,
    AuditSignatureError,
)
from .logger import AuditEvent, canonical_log_bytes, read_events

CLOSE_FORMAT_VERSION: Final[str] = "1"


@dataclass(frozen=True)
class AuditClose:
    close_id: str
    closed_at: str
    event_count: int
    close_hash: str
    signature: str  # JWS serializado

    def _payload_without_signature(self) -> dict[str, Any]:
        return {
            "close_format_version": CLOSE_FORMAT_VERSION,
            "close_id": self.close_id,
            "closed_at": self.closed_at,
            "event_count": self.event_count,
            "close_hash": self.close_hash,
        }

    def to_dict(self) -> dict[str, Any]:
        d = self._payload_without_signature()
        d["signature"] = self.signature
        return d

    def canonical_bytes(self) -> bytes:
        return canonicalize(self.to_dict())


def create_close(
    *,
    log_path: str | Path,
    signing_key: EllipticCurvePrivateKey,
    signing_kid: str,
    signing_x5c: list[str],
    anchor_provider: AnchorProvider | None = None,
) -> AuditClose:
    """Crea un cierre firmado del log completo y lo ancla opcionalmente."""
    events = read_events(log_path)
    if not events:
        raise AuditCloseError("El log está vacío")

    log_bytes = canonical_log_bytes(events)
    close_hash = content_hash_bytes(log_bytes).hex()
    close_id = f"close_{uuid.uuid4().hex[:16]}"
    closed_at = _now_iso()

    skeleton = {
        "close_format_version": CLOSE_FORMAT_VERSION,
        "close_id": close_id,
        "closed_at": closed_at,
        "event_count": len(events),
        "close_hash": close_hash,
    }
    payload_bytes = canonicalize(skeleton)
    jws = sign_detached(
        payload_bytes=payload_bytes,
        private_key=signing_key,
        kid=signing_kid,
        x5c=signing_x5c,
    )

    close = AuditClose(
        close_id=close_id,
        closed_at=closed_at,
        event_count=len(events),
        close_hash=close_hash,
        signature=json.dumps(jws, separators=(",", ":")),
    )

    if anchor_provider is not None:
        anchor_provider.put(close.close_id, log_bytes)

    return close


def write_close(path: str | Path, close: AuditClose) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("ab") as f:
        f.write(close.canonical_bytes() + b"\n")


def read_closes(path: str | Path) -> list[AuditClose]:
    p = Path(path)
    if not p.is_file():
        return []
    closes: list[AuditClose] = []
    with p.open("rb") as f:
        for raw in f:
            raw = raw.rstrip(b"\n")
            if not raw:
                continue
            obj = json.loads(raw)
            closes.append(
                AuditClose(
                    close_id=obj["close_id"],
                    closed_at=obj["closed_at"],
                    event_count=int(obj["event_count"]),
                    close_hash=obj["close_hash"],
                    signature=obj["signature"],
                )
            )
    return closes


@dataclass
class VerifyStep:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class VerifyResult:
    valid: bool
    steps: list[VerifyStep] = field(default_factory=list)
    event_count: int = 0
    close_count: int = 0
    last_event_hash: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "event_count": self.event_count,
            "close_count": self.close_count,
            "last_event_hash": self.last_event_hash,
            "steps": [
                {"name": s.name, "passed": s.passed, "detail": s.detail}
                for s in self.steps
            ],
        }


def verify_audit_log(
    *,
    log_path: str | Path,
    closes: list[AuditClose] | None = None,
    anchor_provider: AnchorProvider | None = None,
) -> VerifyResult:
    """Verifica cadena de eventos, hashes, firmas y anclajes.

    Nunca lanza por fallo de verificación; devuelve valid=False.
    """
    result = VerifyResult(valid=False)
    try:
        events = read_events(log_path)
    except Exception as exc:
        result.steps.append(VerifyStep("read", False, str(exc)))
        return result

    result.event_count = len(events)
    if not events:
        result.steps.append(VerifyStep("read", False, "Log vacío"))
        return result
    result.steps.append(VerifyStep("read", True, f"{len(events)} eventos"))

    # 1. Cadena de eventos
    try:
        _verify_event_chain(events)
        result.steps.append(VerifyStep("chain", True))
    except Exception as exc:
        result.steps.append(VerifyStep("chain", False, str(exc)))
        return result

    # 2. Firmas de eventos
    try:
        _verify_event_signatures(events)
        result.steps.append(VerifyStep("event_signatures", True))
    except Exception as exc:
        result.steps.append(VerifyStep("event_signatures", False, str(exc)))
        return result

    result.last_event_hash = events[-1].event_hash

    # 3. Cierres
    closes = closes or []
    result.close_count = len(closes)
    if closes:
        try:
            _verify_closes(events, closes, anchor_provider)
            result.steps.append(VerifyStep("closes", True, f"{len(closes)} cierres"))
        except Exception as exc:
            result.steps.append(VerifyStep("closes", False, str(exc)))
            return result
    else:
        result.steps.append(VerifyStep("closes", True, "sin cierres declarados"))

    result.valid = all(s.passed for s in result.steps)
    return result


def _verify_event_chain(events: list[AuditEvent]) -> None:
    previous_hash: str | None = None
    for i, e in enumerate(events):
        computed = e.compute_hash()
        if computed != e.event_hash:
            raise AuditChainError(
                f"event_hash no coincide en evento {i} ({e.event_id})"
            )
        if i == 0:
            if e.prev_event_hash != "":
                raise AuditChainError("Genesis con prev_event_hash no vacío")
        else:
            if e.prev_event_hash != previous_hash:
                raise AuditChainError(
                    f"prev_event_hash no coincide en evento {i} ({e.event_id})"
                )
        previous_hash = e.event_hash


def _verify_event_signatures(events: list[AuditEvent]) -> None:
    for i, e in enumerate(events):
        try:
            jws = json.loads(e.signature)
        except json.JSONDecodeError as exc:
            raise AuditSignatureError(
                f"Firma de evento {i} no decodifica: {exc}"
            ) from exc
        payload_bytes = canonicalize(e._payload_without_integrity())
        try:
            verify_detached(jws, payload_bytes)
        except Exception as exc:
            raise AuditSignatureError(
                f"Firma de evento {i} ({e.event_id}) no verifica: {exc}"
            ) from exc


def _verify_closes(
    events: list[AuditEvent],
    closes: list[AuditClose],
    anchor_provider: AnchorProvider | None,
) -> None:
    for c in closes:
        # Verificar firma del cierre
        try:
            jws = json.loads(c.signature)
        except json.JSONDecodeError as exc:
            raise AuditCloseError(
                f"Firma de cierre {c.close_id} no decodifica"
            ) from exc
        payload_bytes = canonicalize(c._payload_without_signature())
        try:
            verify_detached(jws, payload_bytes)
        except Exception as exc:
            raise AuditSignatureError(
                f"Firma de cierre {c.close_id} no verifica: {exc}"
            ) from exc

        # Verificar close_hash contra el prefijo del log
        if c.event_count < 1 or c.event_count > len(events):
            raise AuditCloseError(
                f"event_count fuera de rango en cierre {c.close_id}"
            )
        prefix = events[: c.event_count]
        recomputed = content_hash_bytes(canonical_log_bytes(prefix)).hex()
        if recomputed != c.close_hash:
            raise AuditCloseError(
                f"close_hash no coincide en cierre {c.close_id}"
            )

        # Verificar anclaje externo si hay proveedor
        if anchor_provider is not None:
            anchored = anchor_provider.read(c.close_id)
            anchored_hash = content_hash_bytes(anchored).hex()
            if anchored_hash != c.close_hash:
                raise AuditChainError(
                    f"Anclaje externo de {c.close_id} no coincide"
                )


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
