# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from fastapi import FastAPI

from services.federation.app.routes import router
from shared.config import Settings
from shared.web import create_service_app


def create_app(settings: Settings | None = None) -> FastAPI:
    app = create_service_app(
        title="SENTINEL Federation",
        description="Cross-tenant anonymized threat fingerprint exchange (Phase 10).",
        service_name="sentinel-federation",
        settings=settings,
    )
    app.include_router(router)
    return app
