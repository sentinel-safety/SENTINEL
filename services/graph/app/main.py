# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from fastapi import FastAPI

from services.graph.app.routes import router as graph_router
from shared.config import Settings
from shared.web import create_service_app


def create_app(settings: Settings | None = None) -> FastAPI:
    return create_service_app(
        title="SENTINEL Graph",
        description="Relationship graph maintenance and network-level pattern queries.",
        service_name="sentinel-graph",
        settings=settings,
        routers=(graph_router,),
    )
