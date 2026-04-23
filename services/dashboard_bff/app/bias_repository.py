# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models import Actor, SuspicionProfile, Tenant

_MIN_FLAGGED_TIER = 2


async def bias_rows_by_age_band(
    session: AsyncSession,
) -> list[tuple[str, int, int]]:
    flagged_case = case((SuspicionProfile.tier >= _MIN_FLAGGED_TIER, 1), else_=0)
    stmt = (
        select(
            Actor.claimed_age_band.label("group"),
            func.count(Actor.id).label("total"),
            func.coalesce(func.sum(flagged_case), 0).label("flagged"),
        )
        .select_from(Actor)
        .join(SuspicionProfile, SuspicionProfile.actor_id == Actor.id, isouter=True)
        .group_by(Actor.claimed_age_band)
        .order_by(Actor.claimed_age_band)
    )
    return [(row.group, int(row.total), int(row.flagged)) for row in await session.execute(stmt)]


async def bias_rows_by_jurisdiction(
    session: AsyncSession, *, tenant_id: UUID
) -> list[tuple[str, int, int]]:
    tenant = (await session.execute(select(Tenant).where(Tenant.id == tenant_id))).scalar_one()
    jurisdictions: list[str] = list(tenant.compliance_jurisdictions or ())
    flagged_case = case((SuspicionProfile.tier >= _MIN_FLAGGED_TIER, 1), else_=0)
    stmt = (
        select(
            func.count(Actor.id).label("total"),
            func.coalesce(func.sum(flagged_case), 0).label("flagged"),
        )
        .select_from(Actor)
        .join(SuspicionProfile, SuspicionProfile.actor_id == Actor.id, isouter=True)
    )
    row = (await session.execute(stmt)).one()
    total = int(row.total)
    flagged = int(row.flagged)
    return [(j, total, flagged) for j in jurisdictions]
