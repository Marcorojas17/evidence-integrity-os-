"""Estados y transiciones válidas.

Tres entidades con estados separados:
- orders.status
- payment_events.validation_result
- payment_fulfillments.status
"""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class OrderStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    FAILED_REQUIRES_MANUAL = "failed_requires_manual"
    REJECTED_VALIDATION = "rejected_validation"
    CANCELLED = "cancelled"


class ValidationResult(StrEnum):
    PENDING = "pending"
    APPROVED_READY = "approved_ready"
    REJECTED_NOT_APPROVED_YET = "rejected_not_approved_yet"
    REJECTED_VALIDATION = "rejected_validation"
    REJECTED_SIGNATURE = "rejected_signature"
    REJECTED_REPLAY = "rejected_replay"
    REJECTED_OTHER = "rejected_other"


class FulfillmentStatus(StrEnum):
    QUEUED = "queued"
    EMITTING = "emitting"
    COMPLETED = "completed"
    FAILED = "failed"
    ABANDONED = "abandoned"


class AttemptTrigger(StrEnum):
    WEBHOOK = "webhook"
    MANUAL_OPERATOR = "manual_operator"
    RETRY_SCHEDULED = "retry_scheduled"
    RECOVERY_AFTER_CRASH = "recovery_after_crash"


class AttemptResult(StrEnum):
    SUCCESS = "success"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED_PERMANENT = "failed_permanent"
    ABORTED_CONFLICT = "aborted_conflict"
    ABORTED_CRASH = "aborted_crash"


# Transiciones validas

ORDER_TRANSITIONS: Final[dict[OrderStatus, frozenset[OrderStatus]]] = {
    OrderStatus.PENDING: frozenset({
        OrderStatus.PROCESSING,
        OrderStatus.CANCELLED,
        OrderStatus.REJECTED_VALIDATION,
    }),
    OrderStatus.PROCESSING: frozenset({
        OrderStatus.COMPLETED,
        OrderStatus.FAILED,
    }),
    OrderStatus.FAILED: frozenset({
        OrderStatus.PROCESSING,  # Solo accion manual explicita
    }),
    OrderStatus.FAILED_REQUIRES_MANUAL: frozenset({
        OrderStatus.PROCESSING,  # Solo accion manual explicita
    }),
    OrderStatus.COMPLETED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
    OrderStatus.REJECTED_VALIDATION: frozenset(),
}

FULFILLMENT_TRANSITIONS: Final[dict[FulfillmentStatus, frozenset[FulfillmentStatus]]] = {
    FulfillmentStatus.QUEUED: frozenset({
        FulfillmentStatus.EMITTING,
        FulfillmentStatus.ABANDONED,
    }),
    FulfillmentStatus.EMITTING: frozenset({
        FulfillmentStatus.COMPLETED,
        FulfillmentStatus.FAILED,
        FulfillmentStatus.ABANDONED,
    }),
    FulfillmentStatus.COMPLETED: frozenset(),
    FulfillmentStatus.FAILED: frozenset(),
    FulfillmentStatus.ABANDONED: frozenset(),
}


def can_transition_order(current: OrderStatus, target: OrderStatus) -> bool:
    return target in ORDER_TRANSITIONS.get(current, frozenset())


def can_transition_fulfillment(current: FulfillmentStatus, target: FulfillmentStatus) -> bool:
    return target in FULFILLMENT_TRANSITIONS.get(current, frozenset())
