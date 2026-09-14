"""Webhook de Mercado Pago."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request

from src.payments.webhook import handle_webhook

from .deps import AppContext, get_context

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/mercadopago")
async def mercadopago_webhook(
    request: Request,
    ctx: AppContext = Depends(get_context),
    x_signature: str = Header(default="", alias="x-signature"),
    x_request_id: str = Header(default="", alias="x-request-id"),
) -> dict:
    raw_body = await request.body()

    with ctx.db_pool.connection() as conn:
        result = handle_webhook(
            conn,
            raw_body=raw_body,
            headers={
                "x-signature": x_signature,
                "x-request-id": x_request_id,
            },
            config=ctx.webhook_config,
        )

    # Siempre 200 para que MP no reintente. El cuerpo indica el estado real.
    return result.body
