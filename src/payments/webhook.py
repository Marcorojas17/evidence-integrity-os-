"""Receptor de webhooks de Mercado Pago.

Reglas:
- Responde < 500 ms.
- Verifica firma con hmac.compare_digest.
- Rechaza ts fuera de ventana.
- Encola el evento crudo. No procesa.
- Idempotente por UNIQUE (payment_id, x_request_id).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from .exceptions import SignatureError, SignatureReplayError
from .signature import verify_signature
from .states import ValidationResult

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WebhookConfig:
    """Configuración del webhook."""

    secret: str
    previous_secret: str | None = None
    window_seconds: int = 300


@dataclass(frozen=True)
class WebhookResult:
    """Resultado del procesamiento del webhook."""

    accepted: bool
    status_code: int
    body: dict[str, Any]


def handle_webhook(
    conn: Any,
    *,
    raw_body: bytes,
    headers: dict[str, str],
    config: WebhookConfig,
) -> WebhookResult:
    """Verifica y encola el evento. Nunca procesa en línea.

    No ejecuta hashing, TSA ni PDF. Solo persiste y responde.
    """
    try:
        body = json.loads(raw_body)
    except json.JSONDecodeError:
        return WebhookResult(
            accepted=False,
            status_code=400,
            body={"error": "invalid_json"},
        )

    data_id = _extract_data_id(body)
    if not data_id:
        return WebhookResult(
            accepted=False,
            status_code=400,
            body={"error": "missing_data_id"},
        )

    request_id = headers.get("x-request-id", "")
    signature_header = headers.get("x-signature", "")

    try:
        verify_signature(
            header=signature_header,
            request_id=request_id,
            data_id=data_id,
            secret=config.secret,
            previous_secret=config.previous_secret,
            window_seconds=config.window_seconds,
        )
    except SignatureReplayError as exc:
        logger.warning("Replay rechazado: %s", exc)
        _enqueue_event(
            conn,
            payment_id=data_id,
            request_id=request_id,
            body=body,
            validation_result=ValidationResult.REJECTED_REPLAY.value,
            reason=str(exc),
        )
        return WebhookResult(
            accepted=False,
            status_code=200,
            body={"status": "rejected_replay"},
        )
    except SignatureError as exc:
        logger.warning("Firma invalida: %s", exc)
        return WebhookResult(
            accepted=False,
            status_code=401,
            body={"error": "invalid_signature"},
        )

    _enqueue_event(
        conn,
        payment_id=data_id,
        request_id=request_id,
        body=body,
        validation_result=ValidationResult.PENDING.value,
        reason="",
    )

    return WebhookResult(
        accepted=True,
        status_code=200,
        body={"status": "queued"},
    )


def _extract_data_id(body: dict[str, Any]) -> str | None:
    data = body.get("data")
    if isinstance(data, dict):
        did = data.get("id")
        if isinstance(did, (str, int)):
            return str(did)
    return None


def _enqueue_event(
    conn: Any,
    *,
    payment_id: str,
    request_id: str,
    body: dict[str, Any],
    validation_result: str,
    reason: str,
) -> None:
    """INSERT idempotente. Ignora conflictos por (payment_id, x_request_id)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO payment_events
                (payment_id, x_request_id, mp_status, mp_status_detail,
                 validation_result, validation_reason, raw_payload,
                 order_id, processed_at)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, now())
            ON CONFLICT (payment_id, x_request_id) DO NOTHING
            """,
            (
                payment_id,
                request_id,
                body.get("action", ""),
                body.get("type", ""),
                validation_result,
                reason[:500] if reason else None,
                json.dumps(body),
                body.get("external_reference"),
            ),
        )
