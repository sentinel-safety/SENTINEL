# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from fastapi import FastAPI

from services.explainability.app.routes import router
from shared.config import Settings
from shared.web import create_service_app


def create_app(settings: Settings | None = None) -> FastAPI:
    app = create_service_app(
        title="SENTINEL Explainability",
        description="Human-readable reasoning generation for suspicion scores.",
        service_name="sentinel-explainability",
        settings=settings,
    )
    app.include_router(router)
    return app
