"""Inyección de dependencias de la API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Header, HTTPException, Request, status


@dataclass
class AppContext:
    """Contexto de la aplicación con dependencias ya resueltas."""

    db_pool: Any
    kms: Any
    mp_client: Any
    settings: Any
    webhook_config: Any


def get_context(request: Request) -> AppContext:
    ctx = getattr(request.app.state, "context", None)
    if ctx is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="context not initialized",
        )
    return ctx


def get_request_id(x_request_id: str | None = Header(default=None)) -> str:
    return x_request_id or ""
