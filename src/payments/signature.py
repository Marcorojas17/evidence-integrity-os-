"""Verificación de firma x-signature de Mercado Pago.

Reglas:
- HMAC-SHA256 con el webhook secret.
- Comparación en tiempo constante.
- Rechazo si el timestamp está fuera de la ventana de 5 minutos.
- Soporte de múltiples valores v1 durante rotación de secretos.
- Manifest exacto: id:<data.id>;request-id:<x-request-id>;ts:<ts>;
"""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Final

from .exceptions import SignatureError, SignatureReplayError

DEFAULT_WINDOW_SECONDS: Final[int] = 300


@dataclass(frozen=True)
class ParsedSignature:
    ts: int
    v1_values: tuple[str, ...]


def parse_x_signature(header: str) -> ParsedSignature:
    """Parsea el header x-signature.

    Formato esperado:
        ts=1234567890,v1=hash1,v1=hash2

    Raises:
        SignatureError: si el formato es inválido.
    """
    if not header:
        raise SignatureError("x-signature vacío")

    ts: int | None = None
    v1_values: list[str] = []

    for part in header.split(","):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, _, value = part.partition("=")
        key = key.strip().lower()
        value = value.strip()

        if key == "ts":
            try:
                ts = int(value)
            except ValueError as exc:
                raise SignatureError(f"ts no numérico: {value}") from exc
        elif key == "v1":
            if value:
                v1_values.append(value)

    if ts is None:
        raise SignatureError("x-signature sin ts")
    if not v1_values:
        raise SignatureError("x-signature sin valores v1")

    return ParsedSignature(ts=ts, v1_values=tuple(v1_values))


def build_manifest(data_id: str, request_id: str, ts: int) -> str:
    """Construye el manifest exacto que Mercado Pago firma."""
    return f"id:{data_id};request-id:{request_id};ts:{ts};"


def _compute_hmac(secret: str, manifest: str) -> str:
    return hmac.new(
        secret.encode("utf-8"),
        manifest.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_signature(
    *,
    header: str,
    request_id: str,
    data_id: str,
    secret: str,
    previous_secret: str | None = None,
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
    now_ts: int | None = None,
) -> None:
    """Verifica la firma y la ventana temporal.

    Acepta múltiples v1 y prueba el secreto actual y el anterior (rotación).

    Raises:
        SignatureReplayError: si ts está fuera de la ventana.
        SignatureError: si ningún v1 coincide.
    """
    if not secret:
        raise SignatureError("Webhook secret no configurado")
    if not data_id:
        raise SignatureError("data_id vacío")
    if not request_id:
        raise SignatureError("x-request-id vacío")

    parsed = parse_x_signature(header)

    current = now_ts if now_ts is not None else int(time.time())
    if abs(current - parsed.ts) > window_seconds:
        raise SignatureReplayError(
            f"ts fuera de ventana: {parsed.ts} vs {current}"
        )

    manifest = build_manifest(data_id, request_id, parsed.ts)
    secrets = [secret]
    if previous_secret:
        secrets.append(previous_secret)

    for candidate in secrets:
        expected = _compute_hmac(candidate, manifest)
        for v1 in parsed.v1_values:
            if hmac.compare_digest(expected, v1):
                return

    raise SignatureError("Ningún v1 coincide con la firma esperada")
