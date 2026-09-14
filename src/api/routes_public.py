"""Verificación pública con divulgación mínima."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from .deps import AppContext, get_context
from .schemas import PublicVerifyResponse

router = APIRouter(prefix="/public", tags=["public"])


def _generate_public_token() -> str:
    return secrets.token_urlsafe(16)


@router.get("/{token}", response_model=PublicVerifyResponse)
async def verify_public(
    token: str,
    ctx: AppContext = Depends(get_context),
) -> PublicVerifyResponse:
    """Devuelve información mínima para verificación pública.

    No expone: nombre del titular, tipo de archivo, usuario, fecha exacta.
    """
    with ctx.db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT f.evidence_id, f.status
                  FROM payment_fulfillments f
                 WHERE f.public_token = %s
                   AND f.status = 'completed'
                """,
                (token,),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="not found",
                )

    evidence_id, _ = row
    # El digest completo no se expone; solo un prefijo no correlacionable
    # con otros expedientes del sistema.
    return PublicVerifyResponse(
        valid=True,
        evidence_id=evidence_id,
        manifest_digest_prefix=None,
        issued_at=None,
    )
