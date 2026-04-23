# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from services.dashboard_bff.app.dependencies import require_roles
from services.dashboard_bff.app.schemas import (
    AlertListItem,
    AlertListResponse,
    DashboardRole,
    SessionUser,
)
from shared.db.models import Actor, SuspicionProfile
from shared.db.session import tenant_session

router = APIRouter(prefix="/dashboard/api", tags=["alerts"])

_ALLOWED = require_roles(DashboardRole.ADMIN, DashboardRole.MOD, DashboardRole.AUDITOR)


@router.get("/alerts", response_model=AlertListResponse)
async def list_alerts(
    min_tier: int = Query(default=1, ge=0, le=5),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: SessionUser = Depends(_ALLOWED),
) -> AlertListResponse:
    async with tenant_session(current_user.tenant_id) as session:
        stmt = (
            select(
                SuspicionProfile.actor_id,
                SuspicionProfile.current_score,
                SuspicionProfile.tier,
                SuspicionProfile.tier_entered_at,
                SuspicionProfile.last_updated,
                Actor.claimed_age_band,
            )
            .join(Actor, Actor.id == SuspicionProfile.actor_id)
            .where(SuspicionProfile.tier >= min_tier)
            .order_by(SuspicionProfile.tier.desc(), SuspicionProfile.current_score.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await session.execute(stmt)).all()
    return AlertListResponse(
        alerts=tuple(
            AlertListItem(
                actor_id=r.actor_id,
                current_score=r.current_score,
                tier=r.tier,
                tier_entered_at=r.tier_entered_at,
                last_updated=r.last_updated,
                claimed_age_band=r.claimed_age_band,
            )
            for r in rows
        )
    )
