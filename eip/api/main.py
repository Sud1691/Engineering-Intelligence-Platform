from __future__ import annotations

from fastapi import FastAPI
import structlog

from eip.api.routers import risk, incidents, architecture, cost, compliance
from eip.api import nlq


log = structlog.get_logger()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Engineering Intelligence Platform API",
        version="0.1.0",
        description="Unified API surface for the Engineering Intelligence Platform.",
    )

    app.include_router(risk.router, prefix="/risk", tags=["risk"])
    app.include_router(architecture.router, prefix="/architecture", tags=["architecture"])
    app.include_router(incidents.router, prefix="/incidents", tags=["incidents"])
    app.include_router(cost.router, prefix="/cost", tags=["cost"])
    app.include_router(compliance.router, prefix="/compliance", tags=["compliance"])
    app.include_router(nlq.router, tags=["nlq"])

    return app


app = create_app()

