"""Worker: consume eventos y ejecuta el flujo de dos fases."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Final

from .exceptions import (
    FulfillmentConflictError,
    PaymentNotApprovedYetError,
    PaymentError,
    SignatureError,
    ValidationError,
    WorkerLeaseError,
)
from .fulfillment import (
    claim_fulfillment,
    generate_worker_id,
    mark_completed,
    mark_emitting,
    mark_failed,
    renew_lease,
)
from .states import ValidationResult
from .validation import OrderSnapshot, validate_payment

logger = logging.getLogger(__name__)

LEASE_RENEW_INTERVAL_SECONDS: Final[int] = 60


@dataclass(frozen=True)
class PaymentConfig:
    """Configuración del entorno de pago."""

    collector_id: str
    preference_id: str
    live_mode: bool


EmitCallback = Callable[[str, str], str]
"""Firma: (evidence_id, source_path) -> evidence_id emitido."""


def process_payment(
    conn: Any,
    *,
    payment: dict[str, Any],
    order: OrderSnapshot,
    config: PaymentConfig,
    source_path: str,
    emit: EmitCallback,
) -> dict[str, Any]:
    """Ejecuta el flujo de dos fases.

    FASE A: validación (sin transacción).
    FASE B: fulfillment (transacciones cortas).

    Returns:
        Dict con resultado estructurado.
    """
    # FASE A
    outcome = validate_payment(
        payment,
        order,
        collector_id=config.collector_id,
        preference_id=config.preference_id,
        live_mode=config.live_mode,
    )

    if not outcome.accepted:
        _record_validation_outcome(
            conn,
            payment_id=str(payment.get("id")),
            result=outcome.validation_result,
            reason=outcome.reason,
        )
        return {
            "accepted": False,
            "validation_result": outcome.validation_result,
            "reason": outcome.reason,
        }

    # FASE B
    worker_id = generate_worker_id()
    payment_id = str(payment["id"])

    try:
        claim = claim_fulfillment(
            conn,
            payment_id=payment_id,
            order_id=order.order_id,
            worker_id=worker_id,
        )
    except FulfillmentConflictError as exc:
        logger.info("Fulfillment ya existe: %s", exc)
        return {
            "accepted": True,
            "validation_result": ValidationResult.APPROVED_READY.value,
            "reason": "already_claimed",
        }

    try:
        mark_emitting(conn, claim.fulfillment_id, worker_id)
        evidence_id = emit(order.order_id, source_path)
        mark_completed(conn, claim.fulfillment_id, worker_id, evidence_id)
        return {
            "accepted": True,
            "validation_result": ValidationResult.APPROVED_READY.value,
            "fulfillment_id": claim.fulfillment_id,
            "evidence_id": evidence_id,
        }
    except WorkerLeaseError as exc:
        logger.warning("Lease perdido durante emision: %s", exc)
        return {
            "accepted": True,
            "validation_result": ValidationResult.APPROVED_READY.value,
            "reason": "lease_lost",
        }
    except Exception as exc:
        logger.exception("Error en emision")
        try:
            mark_failed(
                conn,
                claim.fulfillment_id,
                worker_id,
                reason=str(exc),
                permanent=False,
            )
        except Exception:
            logger.exception("No se pudo marcar failed")
        raise


def _record_validation_outcome(
    conn: Any,
    *,
    payment_id: str,
    result: str,
    reason: str,
) -> None:
    """Registra el resultado en payment_events si existe la fila."""
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE payment_events
               SET validation_result = %s,
                   validation_reason = %s,
                   processed_at = now()
             WHERE payment_id = %s
               AND validation_result = 'pending'
            """,
            (result, reason[:500], payment_id),
        )
