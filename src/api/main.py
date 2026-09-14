"""App FastAPI principal."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.payments.webhook import WebhookConfig

from .deps import AppContext
from .middleware import AuditMiddleware, RequestIdMiddleware
from .routes_admin import router as admin_router
from .routes_evidence import router as evidence_router
from .routes_orders import router as orders_router
from .routes_public import router as public_router
from .routes_webhook import router as webhook_router

logger = logging.getLogger(__name__)

UI_STATIC_DIR = Path(__file__).resolve().parents[1] / "ui" / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Inicializa pool de DB, KMS, MP client, etc."""
    # El contexto se inyecta desde el proceso de arranque.
    # Ejemplo:
    #   app.state.context = AppContext(
    #       db_pool=pool,
    #       kms=LocalKMS({...}),
    #       mp_client=MercadoPagoClient(access_token),
    #       settings=settings,
    #       webhook_config=WebhookConfig(secret=...),
    #   )
    yield
    ctx: AppContext | None = getattr(app.state, "context", None)
    if ctx is not None and hasattr(ctx.db_pool, "close"):
        ctx.db_pool.close()


def create_app(*, cors_origins: list[str] | None = None) -> FastAPI:
    app = FastAPI(
        title="Evidence Integrity OS",
        version="0.0.1",
        description=(
            "Plataforma de integridad y trazabilidad de evidencia digital. "
            "No certifica autoría. No emite constancias NOM-151."
        ),
        lifespan=lifespan,
    )

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(AuditMiddleware)

    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["*"],
            allow_credentials=False,
        )

    if UI_STATIC_DIR.is_dir():
        app.mount(
            "/static",
            StaticFiles(directory=str(UI_STATIC_DIR)),
            name="static",
        )

    # Routers de API
    app.include_router(orders_router)
    app.include_router(evidence_router)
    app.include_router(webhook_router)
    app.include_router(public_router)
    app.include_router(admin_router)

    # Router de UI (debe ir al final para no colisionar con rutas de API)
    from src.ui.routes import router as ui_router
    app.include_router(ui_router)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
