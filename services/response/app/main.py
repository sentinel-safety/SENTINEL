# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from fastapi import FastAPI

from services.response.app.routes import router as response_router
from shared.config import Settings
from shared.web import create_service_app


def create_app(settings: Settings | None = None) -> FastAPI:
    return create_service_app(
        title="SENTINEL Response Engine",
        description="Tier calculation and response action orchestration.",
        service_name="sentinel-response",
        settings=settings,
        routers=(response_router,),
    )
