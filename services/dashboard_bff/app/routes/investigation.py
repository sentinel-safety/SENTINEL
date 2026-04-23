# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select

from services.dashboard_bff.app.audit_investigation import record_investigation_access
from services.dashboard_bff.app.dependencies import require_roles
from services.dashboard_bff.app.schemas import (
    DashboardRole,
    InvestigationMessage,
    InvestigationMessagesResponse,
    SessionUser,
)
from shared.db.models import Conversation, Event, SuspicionProfile
from shared.db.session import tenant_session

router = APIRouter(prefix="/dashboard/api/conversations", tags=["investigation"])

_ALLOWED = require_roles(DashboardRole.ADMIN, DashboardRole.MOD)
_MIN_TIER_FOR_ACCESS = 3


@router.get("/{conversation_id}/messages", response_model=InvestigationMessagesResponse)
async def conversation_messages(
    conversation_id: UUID,
    limit: int = Query(default=100, ge=1, le=500),
    x_investigation_reason: str = Header(default="", alias="X-Investigation-Reason"),
    current_user: SessionUser = Depends(_ALLOWED),
) -> InvestigationMessagesResponse:
    reason = x_investigation_reason.strip()
    if not reason:
        raise HTTPException(status_code=400, detail="X-Investigation-Reason header is required")
    async with tenant_session(current_user.tenant_id) as session:
        conv = (
            await session.execute(select(Conversation).where(Conversation.id == conversation_id))
        ).scalar_one_or_none()
        if conv is None:
            raise HTTPException(status_code=404, detail="conversation not found")
        participant_uuids = [UUID(x) for x in conv.participant_actor_ids]
        tiers = (
            (
                await session.execute(
                    select(SuspicionProfile.tier).where(
                        SuspicionProfile.actor_id.in_(participant_uuids)
                    )
                )
            )
            .scalars()
            .all()
        )
        if not any(t >= _MIN_TIER_FOR_ACCESS for t in tiers):
            raise HTTPException(status_code=403, detail="no participant at tier 3+")
        stmt = (
            select(Event)
            .where(Event.conversation_id == conversation_id)
            .order_by(Event.timestamp.asc())
            .limit(limit)
        )
        events = (await session.execute(stmt)).scalars().all()
        await record_investigation_access(
            session,
            tenant_id=current_user.tenant_id,
            user_id=current_user.id,
            role=current_user.role.value,
            conversation_id=conversation_id,
            reason=reason,
        )
    return InvestigationMessagesResponse(
        messages=tuple(
            InvestigationMessage(
                event_id=e.id,
                actor_id=e.actor_id,
                timestamp=e.timestamp,
                type=e.type,
                content_features=e.content_features,
            )
            for e in events
        )
    )
