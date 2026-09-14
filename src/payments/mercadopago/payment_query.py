"""Consulta de pago y verificación de estado."""

from __future__ import annotations

from typing import Any

from src.payments.exceptions import PaymentNotApprovedYetError, ValidationError

from .constants import APPROVED_STATUS_DETAILS, LIVE_MODE_BY_ENV


def is_approved(payment: dict[str, Any]) -> bool:
    """Retorna True si el pago está aprobado y no reembolsado/cancelado."""
    if payment.get("status") != "approved":
        return False
    if payment.get("refunded") is True:
        return False
    if payment.get("cancelled") is True:
        return False
    return True


def assert_payment_matches_order(
    payment: dict[str, Any],
    *,
    order_id: str,
    amount: str,
    currency: str,
    collector_id: str,
    preference_id: str,
    live_mode: bool,
) -> None:
    """Valida los campos del pago contra la orden.

    Raises:
        PaymentNotApprovedYetError: si el pago aún no está aprobado.
        ValidationError: si algún campo no coincide.
    """
    status = payment.get("status")
    if status != "approved":
        raise PaymentNotApprovedYetError(f"status={status}")

    if payment.get("refunded") is True:
        raise ValidationError("payment.refunded=True")

    if payment.get("cancelled") is True:
        raise ValidationError("payment.cancelled=True")

    status_detail = payment.get("status_detail")
    if status_detail not in APPROVED_STATUS_DETAILS:
        raise ValidationError(f"status_detail no aceptado: {status_detail}")

    if str(payment.get("transaction_amount")) != amount:
        raise ValidationError(
            f"amount mismatch: {payment.get('transaction_amount')} != {amount}"
        )

    if payment.get("currency_id") != currency:
        raise ValidationError(
            f"currency mismatch: {payment.get('currency_id')} != {currency}"
        )

    if payment.get("external_reference") != order_id:
        raise ValidationError(
            f"external_reference mismatch: {payment.get('external_reference')} != {order_id}"
        )

    if str(payment.get("collector_id")) != collector_id:
        raise ValidationError(
            f"collector_id mismatch: {payment.get('collector_id')} != {collector_id}"
        )

    if payment.get("preference_id") != preference_id:
        raise ValidationError(
            f"preference_id mismatch: {payment.get('preference_id')} != {preference_id}"
        )

    if bool(payment.get("live_mode")) != live_mode:
        raise ValidationError(
            f"live_mode mismatch: {payment.get('live_mode')} != {live_mode}"
        )

    if not payment.get("date_approved"):
        raise ValidationError("date_approved ausente")
