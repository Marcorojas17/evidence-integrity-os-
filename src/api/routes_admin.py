"""Endpoints administrativos (requieren autenticación)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.payments.recovery import (
    claim_orphan_for_recovery,
    find_orphans,
    mark_abandoned,
)
from src.payments.fulfillment import generate_worker_id

from .deps import AppContext, get_context

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(token: str, ctx: AppContext) -> None:
    if not ctx.settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin token not configured",
        )
    import hmac
    if not hmac.compare_digest(token, ctx.settings.admin_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
        )


@router.post("/recover")
async def recover_orphans(
    ctx: AppContext = Depends(get_context),
    x_admin_token: str = Header(default="", alias="x-admin-token"),
) -> dict:
    _require_admin(x_admin_token, ctx)

    with ctx.db_pool.connection() as conn:
        orphans = find_orphans(conn, limit=100)
        worker_id = generate_worker_id()
        claimed = 0
        for orphan in orphans:
            if claim_orphan_for_recovery(conn, orphan, worker_id):
                claimed += 1

    return {"found": len(orphans), "claimed": claimed}


@router.post("/abandon")
async def abandon_orphan(
    fulfillment_id: int,
    reason: str,
    ctx: AppContext = Depends(get_context),
    x_admin_token: str = Header(default="", alias="x-admin-token"),
) -> dict:
    _require_admin(x_admin_token, ctx)

    with ctx.db_pool.connection() as conn:
        from src.payments.recovery import OrphanFulfillment
        orphan = OrphanFulfillment(
            fulfillment_id=fulfillment_id,
            order_id="",
            payment_id="",
            previous_worker_id=None,
            status="",
        )
        mark_abandoned(conn, orphan, reason)
    return {"fulfillment_id": fulfillment_id, "abandoned": True}
