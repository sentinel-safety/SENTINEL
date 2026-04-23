# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import AsyncIterator, Callable, Iterable
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from shared.config import Settings, get_settings
from shared.observability import configure_observability, instrument_fastapi
from shared.web.health import router as meta_router
from shared.web.middleware import RequestIdMiddleware

DEFAULT_VERSION = "0.0.1"

_LifespanFn = Callable[[FastAPI], AsyncIterator[None]]


def create_service_app(
    *,
    title: str,
    description: str,
    service_name: str,
    settings: Settings | None = None,
    version: str = DEFAULT_VERSION,
    routers: Iterable[APIRouter] = (),
    lifespan: _LifespanFn | None = None,
) -> FastAPI:
    resolved = settings or get_settings()
    resolved = resolved.model_copy(update={"service_name": service_name})
    configure_observability(resolved)

    @asynccontextmanager
    async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
        if lifespan is not None:
            async with lifespan(app):  # type: ignore[attr-defined]
                yield
        else:
            yield

    app = FastAPI(title=title, version=version, description=description, lifespan=_lifespan)
    app.state.settings = resolved
    app.add_middleware(RequestIdMiddleware)
    app.include_router(meta_router)
    for router in routers:
        app.include_router(router)
    instrument_fastapi(app)
    return app
