# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from fastapi import FastAPI

from services.synthetic_data.app.routes import router
from shared.config import Settings
from shared.web import create_service_app


def create_app(settings: Settings | None = None) -> FastAPI:
    return create_service_app(
        title="SENTINEL Synthetic Data",
        description="Synthetic predator-minor conversation pipeline for model training (Phase 11).",
        service_name="sentinel-synthetic-data",
        settings=settings,
        routers=(router,),
    )
