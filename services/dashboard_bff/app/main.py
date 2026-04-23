# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from fastapi import FastAPI

from services.dashboard_bff.app.routes import all_routers
from shared.config import Settings
from shared.web import create_service_app


def create_app(settings: Settings | None = None) -> FastAPI:
    return create_service_app(
        title="SENTINEL Dashboard BFF",
        description="Backend-for-frontend for the moderator dashboard.",
        service_name="sentinel-dashboard-bff",
        settings=settings,
        routers=all_routers(),
    )
