# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from services.ingestion.app.clients import DownstreamClients
from services.ingestion.app.routes import router as ingest_router
from shared.config import Settings
from shared.web.factory import create_service_app


def create_app(settings: Settings | None = None) -> FastAPI:
    app = create_service_app(
        title="SENTINEL Ingestion",
        description="HTTP event intake and pipeline orchestration.",
        service_name="sentinel-ingestion",
        settings=settings,
        routers=(ingest_router,),
    )
    resolved = app.state.settings
    http = httpx.AsyncClient(timeout=5.0)
    app.state.http_client = http
    app.state.downstream_clients = DownstreamClients.from_settings(resolved, http)

    @asynccontextmanager
    async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        await _app.state.http_client.aclose()

    app.router.lifespan_context = _lifespan
    return app
