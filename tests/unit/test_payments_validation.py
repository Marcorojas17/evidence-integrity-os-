"""Smoke tests de FASE A."""

from __future__ import annotations

from src.payments.validation import OrderSnapshot, validate_payment

ORDER = OrderSnapshot(
    order_id="ord_001",
    amount="19.00",
    currency="MXN",
    product_code="express",
)

CONFIG = dict(
    collector_id="999",
    preference_id="pref_001",
    live_mode=False,
)


def _approved_payment() -> dict:
    return {
        "id": "123",
        "status": "approved",
        "status_detail": "accredited",
        "transaction_amount": 19.00,
        "currency_id": "MXN",
        "external_reference": "ord_001",
        "collector_id": 999,
        "preference_id": "pref_001",
        "refunded": False,
        "cancelled": False,
        "date_approved": "2026-09-13T12:00:00.000Z",
        "live_mode": False,
    }


def test_accepts_valid_payment() -> None:
    outcome = validate_payment(_approved_payment(), ORDER, **CONFIG)
    assert outcome.accepted


def test_rejects_not_approved_yet() -> None:
    p = _approved_payment()
    p["status"] = "pending"
    outcome = validate_payment(p, ORDER, **CONFIG)
    assert not outcome.accepted
    assert outcome.validation_result == "rejected_not_approved_yet"


def test_rejects_amount_mismatch() -> None:
    p = _approved_payment()
    p["transaction_amount"] = 15.00
    outcome = validate_payment(p, ORDER, **CONFIG)
    assert not outcome.accepted
    assert outcome.validation_result == "rejected_validation"


def test_rejects_refunded() -> None:
    p = _approved_payment()
    p["refunded"] = True
    outcome = validate_payment(p, ORDER, **CONFIG)
    assert not outcome.accepted
    assert outcome.validation_result == "rejected_validation"


def test_rejects_wrong_collector() -> None:
    p = _approved_payment()
    p["collector_id"] = 1
    outcome = validate_payment(p, ORDER, **CONFIG)
    assert not outcome.accepted


def test_rejects_live_mode_mismatch() -> None:
    p = _approved_payment()
    p["live_mode"] = True
    outcome = validate_payment(p, ORDER, **CONFIG)
    assert not outcome.accepted
