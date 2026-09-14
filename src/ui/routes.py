"""Rutas de la interfaz web (server-side rendering)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.api.deps import AppContext, get_context

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter(tags=["ui"])


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "verify.html",
        {"title": "Inicio"},
    )


@router.get("/verify", response_class=HTMLResponse)
async def verify_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "verify.html",
        {"title": "Verificar paquete"},
    )


@router.get("/orders/{order_id}", response_class=HTMLResponse)
async def order_page(
    order_id: str,
    request: Request,
    ctx: AppContext = Depends(get_context),
) -> HTMLResponse:
    with ctx.db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT o.order_id, o.status, o.product_code, o.amount,
                       o.currency, o.created_at, o.updated_at,
                       f.evidence_id
                  FROM orders o
                  LEFT JOIN payment_fulfillments f
                    ON f.order_id = o.order_id
                 WHERE o.order_id = %s
                """,
                (order_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="order not found",
                )

    order = {
        "order_id": row[0],
        "status": row[1],
        "product_code": row[2],
        "amount": str(row[3]),
        "currency": row[4],
        "created_at": row[5].isoformat() if row[5] else "",
        "updated_at": row[6].isoformat() if row[6] else "",
        "evidence_id": row[7],
    }

    return templates.TemplateResponse(
        request,
        "order.html",
        {"order": order, "title": f"Orden {order_id}"},
    )


@router.get("/checkout/success", response_class=HTMLResponse)
async def checkout_success(
    request: Request,
    order_id: str = "",
    payment_id: str = "",
    status: str = "processing",
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "checkout_success.html",
        {
            "order_id": order_id,
            "payment_id": payment_id,
            "status": status,
        },
    )


@router.get("/checkout/pending", response_class=HTMLResponse)
async def checkout_pending(
    request: Request,
    order_id: str = "",
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "checkout_pending.html",
        {"order_id": order_id},
    )


@router.get("/checkout/failure", response_class=HTMLResponse)
async def checkout_failure(
    request: Request,
    order_id: str = "",
    status: str = "cancelled",
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "checkout_failure.html",
        {"order_id": order_id, "status": status},
    )
