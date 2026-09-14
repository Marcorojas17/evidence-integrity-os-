"""FASE A: validación del pago. Sin transacción, sin locks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .exceptions import (
    PaymentNotApprovedYetError,
    PaymentError,
    ValidationError,
)
from .mercadopago.payment_query import assert_payment_matches_order


@dataclass(frozen=True)
class OrderSnapshot:
    """Datos de la orden necesarios para validar el pago."""

    order_id: str
    amount: str
    currency: str
    product_code: str


@dataclass(frozen=True)
class ValidationOutcome:
    """Resultado de la FASE A."""

    accepted: bool
    reason: str
    validation_result: str  # valor de ValidationResult


def validate_payment(
    payment: dict[str, Any],
    order: OrderSnapshot,
    *,
    collector_id: str,
    preference_id: str,
    live_mode: bool,
) -> ValidationOutcome:
    """Valida el pago contra la orden.

    No toca base de datos. Sin transacción, sin locks.
    """
    try:
        assert_payment_matches_order(
            payment,
            order_id=order.order_id,
            amount=order.amount,
            currency=order.currency,
            collector_id=collector_id,
            preference_id=preference_id,
            live_mode=live_mode,
        )
    except PaymentNotApprovedYetError as exc:
        return ValidationOutcome(
            accepted=False,
            reason=str(exc),
            validation_result="rejected_not_approved_yet",
        )
    except ValidationError as exc:
        return ValidationOutcome(
            accepted=False,
            reason=str(exc),
            validation_result="rejected_validation",
        )
    except PaymentError as exc:
        return ValidationOutcome(
            accepted=False,
            reason=str(exc),
            validation_result="rejected_other",
        )

    return ValidationOutcome(
        accepted=True,
        reason="validacion ok",
        validation_result="approved_ready",
    )
