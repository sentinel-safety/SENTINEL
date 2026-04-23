# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

from services.dashboard_bff.app.dependencies import require_roles
from services.dashboard_bff.app.schemas import (
    ActorDetail,
    DashboardRole,
    EventListResponse,
    EventSummary,
    ReasoningEntry,
    ReasoningListResponse,
    SessionUser,
)
from shared.db.models import Actor, Event, Reasoning, SuspicionProfile
from shared.db.session import tenant_session

router = APIRouter(prefix="/dashboard/api/actors", tags=["actors"])

_ALLOWED = require_roles(DashboardRole.ADMIN, DashboardRole.MOD, DashboardRole.AUDITOR)


@router.get("/{actor_id}", response_model=ActorDetail)
async def actor_detail(
    actor_id: UUID, current_user: SessionUser = Depends(_ALLOWED)
) -> ActorDetail:
    async with tenant_session(current_user.tenant_id) as session:
        actor = (
            await session.execute(select(Actor).where(Actor.id == actor_id))
        ).scalar_one_or_none()
        if actor is None:
            raise HTTPException(status_code=404, detail="actor not found")
        profile = (
            await session.execute(
                select(SuspicionProfile).where(SuspicionProfile.actor_id == actor_id)
            )
        ).scalar_one_or_none()
    return ActorDetail(
        actor_id=actor.id,
        tenant_id=actor.tenant_id,
        claimed_age_band=actor.claimed_age_band,
        account_created_at=actor.account_created_at,
        current_score=profile.current_score if profile else None,
        tier=profile.tier if profile else None,
        tier_entered_at=profile.tier_entered_at if profile else None,
    )


@router.get("/{actor_id}/events", response_model=EventListResponse)
async def actor_events(
    actor_id: UUID,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: SessionUser = Depends(_ALLOWED),
) -> EventListResponse:
    async with tenant_session(current_user.tenant_id) as session:
        stmt = (
            select(
                Event.id,
                Event.conversation_id,
                Event.timestamp,
                Event.type,
                Event.score_delta,
            )
            .where(Event.actor_id == actor_id)
            .order_by(Event.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = (await session.execute(stmt)).all()
    return EventListResponse(
        events=tuple(
            EventSummary(
                id=r.id,
                conversation_id=r.conversation_id,
                timestamp=r.timestamp,
                type=r.type,
                score_delta=r.score_delta,
            )
            for r in rows
        )
    )


@router.get("/{actor_id}/reasoning", response_model=ReasoningListResponse)
async def actor_reasoning(
    actor_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: SessionUser = Depends(_ALLOWED),
) -> ReasoningListResponse:
    async with tenant_session(current_user.tenant_id) as session:
        stmt = (
            select(Reasoning)
            .where(Reasoning.actor_id == actor_id)
            .order_by(Reasoning.created_at.desc())
            .limit(limit)
        )
        rows = (await session.execute(stmt)).scalars().all()
    return ReasoningListResponse(
        reasoning=tuple(
            ReasoningEntry(
                id=r.id,
                event_id=r.event_id,
                reasoning_json=r.reasoning_json,
                created_at=r.created_at,
            )
            for r in rows
        )
    )
