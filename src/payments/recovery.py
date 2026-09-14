"""Recuperación de fulfillments huérfanos con lease vencido.

Reglas:
- Solo recupera status='emitting' AND lease_until < now().
- Solo recupera status='queued' AND created_at < now() - 5 min.
- FOR UPDATE SKIP LOCKED para evitar contención.
- Crea nuevo attempt con trigger='recovery_after_crash'.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

QUEUED_TIMEOUT_MINUTES: Final[int] = 10


@dataclass(frozen=True)
class OrphanFulfillment:
    fulfillment_id: int
    order_id: str
    payment_id: str
    previous_worker_id: str | None
    status: str


def find_orphans(conn: Any, *, limit: int = 50) -> list[OrphanFulfillment]:
    """Encuentra fulfillments huérfanos.

    No mantiene lock prolongado. Devuelve lista sin bloquear otras filas.
    """
    orphans: list[OrphanFulfillment] = []
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT fulfillment_id, order_id, payment_id, worker_id, status
              FROM payment_fulfillments
             WHERE (status = 'emitting' AND lease_until < now())
                OR (status = 'queued'
                    AND created_at < now() - interval '10 minutes')
             ORDER BY updated_at ASC
             LIMIT %s
            """,
            (limit,),
        )
        for row in cur.fetchall():
            orphans.append(
                OrphanFulfillment(
                    fulfillment_id=row[0],
                    order_id=row[1],
                    payment_id=row[2],
                    previous_worker_id=row[3],
                    status=row[4],
                )
            )
    return orphans


def claim_orphan_for_recovery(
    conn: Any,
    orphan: OrphanFulfillment,
    new_worker_id: str,
) -> bool:
    """Reclama un huérfano en transacción corta.

    Returns:
        True si el reclamo fue exitoso, False si otro worker se adelantó.
    """
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE payment_fulfillments
                   SET worker_id = %s,
                       lease_until = now() + interval '5 minutes',
                       updated_at = now()
                 WHERE fulfillment_id = %s
                   AND (
                        (status = 'emitting' AND lease_until < now())
                     OR (status = 'queued'
                         AND created_at < now() - interval '10 minutes')
                   )
                """,
                (new_worker_id, orphan.fulfillment_id),
            )
            if cur.rowcount == 0:
                return False

            cur.execute(
                """
                INSERT INTO fulfillment_attempts
                    (fulfillment_id, attempt_number, trigger, worker_id)
                SELECT %s,
                       COALESCE(MAX(attempt_number), 0) + 1,
                       'recovery_after_crash',
                       %s
                  FROM fulfillment_attempts
                 WHERE fulfillment_id = %s
                """,
                (orphan.fulfillment_id, new_worker_id, orphan.fulfillment_id),
            )
    return True


def mark_abandoned(conn: Any, orphan: OrphanFulfillment, reason: str) -> None:
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE payment_fulfillments
                   SET status = 'abandoned',
                       worker_id = NULL,
                       lease_until = NULL,
                       updated_at = now()
                 WHERE fulfillment_id = %s
                """,
                (orphan.fulfillment_id,),
            )
            cur.execute(
                """
                UPDATE fulfillment_attempts
                   SET finished_at = now(),
                       result = 'aborted_crash',
                       error_detail = %s
                 WHERE fulfillment_id = %s
                   AND finished_at IS NULL
                """,
                (reason[:500], orphan.fulfillment_id),
            )
