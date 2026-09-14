"""Endpoints de evidencia (verificación y eliminación)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from src.evidence.verifier import verify_evidence_package

from .deps import AppContext, get_context
from .schemas import EvidenceVerifyResponse

router = APIRouter(prefix="/evidence", tags=["evidence"])

MAX_PACKAGE_BYTES = 50 * 1024 * 1024  # 50 MB


@router.post("/verify", response_model=EvidenceVerifyResponse)
async def verify_uploaded_package(
    file: UploadFile = File(...),
) -> EvidenceVerifyResponse:
    raw = await file.read()
    if len(raw) > MAX_PACKAGE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="package too large",
        )

    result = verify_evidence_package(raw)
    return EvidenceVerifyResponse(**result.to_dict())


@router.delete("/{evidence_id}", status_code=status.HTTP_202_ACCEPTED)
async def request_deletion(
    evidence_id: str,
    ctx: AppContext = Depends(get_context),
) -> dict:
    """Marca la evidencia para eliminación de datos identificables.

    No borra hashes ni tokens de tiempo. Solo desvincula datos personales.
    """
    with ctx.db_pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE payment_fulfillments
                   SET status = 'abandoned', updated_at = now()
                 WHERE evidence_id = %s
                   AND status = 'completed'
                """,
                (evidence_id,),
            )
            affected = cur.rowcount
    return {"evidence_id": evidence_id, "marked": affected > 0}
