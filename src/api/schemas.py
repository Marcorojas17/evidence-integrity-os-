"""Modelos Pydantic para request/response de la API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class OrderCreateRequest(BaseModel):
    product_code: str = Field(..., min_length=1, max_length=32)
    amount: str = Field(..., pattern=r"^[0-9]+(\.[0-9]{1,2})?$")
    currency: str = Field(default="MXN", pattern=r"^[A-Z]{3}$")
    user_id: str = Field(..., min_length=1, max_length=64)


class OrderCreateResponse(BaseModel):
    order_id: str
    init_point: str
    preference_id: str


class OrderStatusResponse(BaseModel):
    order_id: str
    status: str
    product_code: str
    amount: str
    currency: str
    created_at: str
    updated_at: str


class EvidenceVerifyResponse(BaseModel):
    valid: bool
    evidence_id: str | None = None
    manifest_digest: str | None = None
    tsa_gen_time: str | None = None
    revocation_state: str | None = None
    steps: list[dict[str, Any]] = []


class PublicVerifyResponse(BaseModel):
    valid: bool
    evidence_id: str | None = None
    manifest_digest_prefix: str | None = None
    issued_at: str | None = None
