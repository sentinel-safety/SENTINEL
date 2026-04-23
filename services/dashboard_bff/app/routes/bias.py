# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from services.dashboard_bff.app.bias_repository import (
    bias_rows_by_age_band,
    bias_rows_by_jurisdiction,
)
from services.dashboard_bff.app.dependencies import require_roles
from services.dashboard_bff.app.schemas import (
    BiasAuditResponse,
    BiasGroupRow,
    DashboardRole,
    SessionUser,
)
from shared.db.session import tenant_session

router = APIRouter(prefix="/dashboard/api", tags=["bias"])

_ALLOWED = require_roles(DashboardRole.ADMIN, DashboardRole.AUDITOR)


def _row(group: str, total: int, flagged: int) -> BiasGroupRow:
    rate = (flagged / total) if total > 0 else 0.0
    return BiasGroupRow(
        group=group,
        total_actors=total,
        total_flagged=flagged,
        flag_rate=round(rate, 6),
    )


@router.get("/bias-audit", response_model=BiasAuditResponse)
async def bias_audit(
    group_by: str = Query(default="age_band", pattern="^(age_band|jurisdiction)$"),
    current_user: SessionUser = Depends(_ALLOWED),
) -> BiasAuditResponse:
    async with tenant_session(current_user.tenant_id) as session:
        if group_by == "age_band":
            raw = await bias_rows_by_age_band(session)
        else:
            raw = await bias_rows_by_jurisdiction(session, tenant_id=current_user.tenant_id)
    return BiasAuditResponse(group_by=group_by, rows=tuple(_row(g, t, f) for g, t, f in raw))
