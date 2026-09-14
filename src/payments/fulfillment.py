"""FASE B: creación idempotente del fulfillment y emisión.

Reglas:
- INSERT con ON CONFLICT (payment_id) DO NOTHING.
- Si no retorna fila, otro worker ya reclamó.
- worker_id + lease_until para recuperación sin duplicar.
- Transacciones cortas. Nunca mantener lock durante I/O externo.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Final

from .exceptions import FulfillmentConflictError, WorkerLeaseError
from .states import FulfillmentStatus

LEASE_DURATION_SECONDS: Final[int] = 300  # 5 minutos


@dataclass(frozen=True)
class FulfillmentClaim:
    fulfillment_id: int
    payment_id: str
    order_id: str


def generate_worker_id() -> str:
    return f"worker_{uuid.uuid4().hex[:12]}"


def claim_fulfillment(
    conn: Any,
    *,
    payment_id: str,
    order_id: str,
    worker_id: str,
) -> FulfillmentClaim:
    """FASE B.1: reclama el fulfillment en una transacción corta.

    Raises:
        FulfillmentConflictError: si otro worker ya reclamó.
    """
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO payment_fulfillments
                    (payment_id, order_id, status, worker_id, lease_until)
                VALUES
                    (%s, %s, %s, %s, now() + interval '5 minutes')
                ON CONFLICT (payment_id) DO NOTHING
                RETURNING fulfillment_id
                """,
                (payment_id, order_id, FulfillmentStatus.QUEUED.value, worker_id),
            )
            row = cur.fetchone()
            if row is None:
                raise FulfillmentConflictError(
                    f"Fulfillment ya existe para payment_id={payment_id}"
                )
            fulfillment_id = row[0]

            cur.execute(
                """
                INSERT INTO fulfillment_attempts
                    (fulfillment_id, attempt_number, trigger, worker_id)
                VALUES (%s, 1, 'webhook', %s)
                """,
                (fulfillment_id, worker_id),
            )

            cur.execute(
                """
                UPDATE orders
                   SET status = %s, updated_at = now()
                 WHERE order_id = %s
                """,
                ("processing", order_id),
            )

    return FulfillmentClaim(
        fulfillment_id=fulfillment_id,
        payment_id=payment_id,
        order_id=order_id,
    )


def renew_lease(conn: Any, fulfillment_id: int, worker_id: str) -> None:
    """Renueva el lease. Si no afecta filas, el worker ya no es dueño."""
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE payment_fulfillments
               SET lease_until = now() + interval '5 minutes',
                   updated_at = now()
             WHERE fulfillment_id = %s
               AND worker_id = %s
               AND status = %s
            """,
            (fulfillment_id, worker_id, FulfillmentStatus.EMITTING.value),
        )
        if cur.rowcount == 0:
            raise WorkerLeaseError(
                f"Lease perdido para fulfillment_id={fulfillment_id}"
            )


def mark_emitting(conn: Any, fulfillment_id: int, worker_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE payment_fulfillments
               SET status = %s,
                   worker_id = %s,
                   lease_until = now() + interval '5 minutes',
                   updated_at = now()
             WHERE fulfillment_id = %s
               AND status = %s
            """,
            (
                FulfillmentStatus.EMITTING.value,
                worker_id,
                fulfillment_id,
                FulfillmentStatus.QUEUED.value,
            ),
        )
        if cur.rowcount == 0:
            raise FulfillmentConflictError(
                f"No se pudo marcar emitting: {fulfillment_id}"
            )


def mark_completed(
    conn: Any,
    fulfillment_id: int,
    worker_id: str,
    evidence_id: str,
) -> None:
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE payment_fulfillments
                   SET status = %s,
                       evidence_id = %s,
                       updated_at = now()
                 WHERE fulfillment_id = %s
                   AND worker_id = %s
                """,
                (
                    FulfillmentStatus.COMPLETED.value,
                    evidence_id,
                    fulfillment_id,
                    worker_id,
                ),
            )
            if cur.rowcount == 0:
                raise WorkerLeaseError(f"Lease perdido: {fulfillment_id}")

            cur.execute(
                """
                UPDATE fulfillment_attempts
                   SET finished_at = now(),
                       result = 'success'
                 WHERE fulfillment_id = %s
                   AND finished_at IS NULL
                """,
                (fulfillment_id,),
            )

            cur.execute(
                """
                UPDATE orders
                   SET status = %s, updated_at = now()
                 WHERE order_id = (
                    SELECT order_id FROM payment_fulfillments
                     WHERE fulfillment_id = %s
                 )
                """,
                ("completed", fulfillment_id),
            )


def mark_failed(
    conn: Any,
    fulfillment_id: int,
    worker_id: str,
    reason: str,
    *,
    permanent: bool = False,
) -> None:
    with conn.transaction():
        with conn.cursor() as cur:
            new_status = (
                FulfillmentStatus.FAILED.value
                if permanent
                else FulfillmentStatus.QUEUED.value  # vuelve a cola
            )
            cur.execute(
                """
                UPDATE payment_fulfillments
                   SET status = %s,
                       worker_id = NULL,
                       lease_until = NULL,
                       updated_at = now()
                 WHERE fulfillment_id = %s
                   AND worker_id = %s
                """,
                (new_status, fulfillment_id, worker_id),
            )
            cur.execute(
                """
                UPDATE fulfillment_attempts
                   SET finished_at = now(),
                       result = %s,
                       error_detail = %s
                 WHERE fulfillment_id = %s
                   AND finished_at IS NULL
                """,
                (
                    "failed_permanent" if permanent else "failed_retryable",
                    reason[:500],
                    fulfillment_id,
                ),
            )
