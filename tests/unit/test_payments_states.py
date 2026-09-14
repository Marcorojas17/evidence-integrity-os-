"""Smoke tests de estados y transiciones."""

from __future__ import annotations

from src.payments.states import (
    FulfillmentStatus,
    OrderStatus,
    can_transition_fulfillment,
    can_transition_order,
)


def test_order_pending_to_processing() -> None:
    assert can_transition_order(OrderStatus.PENDING, OrderStatus.PROCESSING)


def test_order_completed_is_terminal() -> None:
    assert not can_transition_order(OrderStatus.COMPLETED, OrderStatus.PROCESSING)


def test_order_failed_to_processing_only_manual() -> None:
    # Permitido por transicion, pero el worker NUNCA lo hace automaticamente.
    assert can_transition_order(OrderStatus.FAILED, OrderStatus.PROCESSING)


def test_fulfillment_queued_to_emitting() -> None:
    assert can_transition_fulfillment(
        FulfillmentStatus.QUEUED, FulfillmentStatus.EMITTING
    )


def test_fulfillment_completed_is_terminal() -> None:
    assert not can_transition_fulfillment(
        FulfillmentStatus.COMPLETED, FulfillmentStatus.EMITTING
    )
