# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from fastapi import FastAPI, HTTPException

from shared.config import Settings
from shared.web.factory import create_service_app


def create_app(settings: Settings | None = None) -> FastAPI:
    app = create_service_app(
        title="SENTINEL Classifier First Pass (retired)",
        description="Retired in Phase 2. All routes return 410 Gone.",
        service_name="sentinel-classifier-first-pass",
        settings=settings,
    )

    @app.post("/internal/classify")
    async def gone() -> None:
        raise HTTPException(
            status_code=410,
            detail="classifier_first_pass retired; use /internal/detect on patterns",
        )

    return app
