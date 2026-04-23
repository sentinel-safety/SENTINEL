# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from fastapi import APIRouter


def all_routers() -> tuple[APIRouter, ...]:
    from services.dashboard_bff.app.routes.actors import router as actors_router
    from services.dashboard_bff.app.routes.alerts import router as alerts_router
    from services.dashboard_bff.app.routes.audit import router as audit_router
    from services.dashboard_bff.app.routes.auth import router as auth_router
    from services.dashboard_bff.app.routes.bias import router as bias_router
    from services.dashboard_bff.app.routes.compliance import router as compliance_router
    from services.dashboard_bff.app.routes.federation import router as federation_router
    from services.dashboard_bff.app.routes.honeypot import router as honeypot_router
    from services.dashboard_bff.app.routes.investigation import (
        router as investigation_router,
    )
    from services.dashboard_bff.app.routes.security import router as security_router
    from services.dashboard_bff.app.routes.tenant import router as tenant_router

    return (
        auth_router,
        alerts_router,
        actors_router,
        investigation_router,
        audit_router,
        compliance_router,
        bias_router,
        tenant_router,
        honeypot_router,
        federation_router,
        security_router,
    )
