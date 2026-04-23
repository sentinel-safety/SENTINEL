# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from fastapi import FastAPI

from services.preprocessing.app.routes import router as preprocess_router
from shared.config import Settings
from shared.web.factory import create_service_app


def create_app(settings: Settings | None = None) -> FastAPI:
    return create_service_app(
        title="SENTINEL Preprocessing",
        description="Text normalization and feature extraction.",
        service_name="sentinel-preprocessing",
        settings=settings,
        routers=(preprocess_router,),
    )
