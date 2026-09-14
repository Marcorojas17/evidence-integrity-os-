"""Endpoints de órdenes internas."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from .deps import AppContext, get_context
from .schemas import OrderCreateRequest, OrderCreateResponse, OrderStatusResponse

router = APIRouter(prefix="/orders", tags=["orders"])


def _new_order_id() -> str:
    return f"ord_{datetime.now(timezone.utc).strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}"


@router.post("", response_model=OrderCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreateRequest,
    ctx: AppContext = Depends(get_context),
) -> OrderCreateResponse:
    order_id = _new_order_id()

    with ctx.db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO orders (order_id, user_id, product_code, amount, currency)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    order_id,
                    payload.user_id,
                    payload.product_code,
                    payload.amount,
                    payload.currency,
                ),
            )

    idempotency_key = uuid.uuid4().hex
    preference_payload = {
        "items": [
            {
                "title": f"Evidence Integrity - {payload.product_code}",
                "quantity": 1,
                "currency_id": payload.currency,
                "unit_price": float(payload.amount),
            }
        ],
        "external_reference": order_id,
        "notification_url": f"{ctx.settings.app_base_url}/webhook/mercadopago",
    }

    try:
        pref = ctx.mp_client.create_preference(preference_payload, idempotency_key)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"preference creation failed: {exc}",
        ) from exc

    return OrderCreateResponse(
        order_id=order_id,
        init_point=pref.get("init_point", ""),
        preference_id=pref.get("id", ""),
    )


@router.get("/{order_id}", response_model=OrderStatusResponse)
async def get_order(
    order_id: str,
    ctx: AppContext = Depends(get_context),
) -> OrderStatusResponse:
    with ctx.db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT order_id, status, product_code, amount, currency,
                       created_at, updated_at
                  FROM orders
                 WHERE order_id = %s
                """,
                (order_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="order not found",
                )
    return OrderStatusResponse(
        order_id=row[0],
        status=row[1],
        product_code=row[2],
        amount=str(row[3]),
        currency=row[4],
        created_at=row[5].isoformat(),
        updated_at=row[6].isoformat(),
    )
