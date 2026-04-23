# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI

from services.honeypot.app.routes import router
from shared.config import Settings
from shared.honeypot.personas import PersonaLoader
from shared.web import create_service_app


def create_app(settings: Settings | None = None) -> FastAPI:
    app = create_service_app(
        title="SENTINEL Honeypot",
        description="Strictly-gated synthetic-persona decoy for tier-3+ actors.",
        service_name="sentinel-honeypot",
        settings=settings,
    )
    resolved = app.state.settings
    app.state.persona_loader = PersonaLoader(resolved.honeypot_personas_dir)
    app.include_router(router)

    @asynccontextmanager
    async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
        client: aioredis.Redis[bytes] = aioredis.from_url(
            resolved.redis_dsn, encoding="utf-8", decode_responses=False
        )
        _app.state.redis = client
        try:
            yield
        finally:
            await client.aclose()  # type: ignore[attr-defined]

    app.router.lifespan_context = _lifespan
    return app
