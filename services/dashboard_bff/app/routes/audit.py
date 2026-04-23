# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from services.dashboard_bff.app.dependencies import require_roles
from services.dashboard_bff.app.schemas import (
    AuditEntryItem,
    AuditEntryListResponse,
    DashboardRole,
    SessionUser,
)
from shared.db.models import AuditLogEntry
from shared.db.session import tenant_session

router = APIRouter(prefix="/dashboard/api", tags=["audit"])

_ALLOWED = require_roles(DashboardRole.ADMIN, DashboardRole.AUDITOR)


@router.get("/audit-log", response_model=AuditEntryListResponse)
async def audit_log(
    actor_id: UUID | None = Query(default=None),
    event_type: str | None = Query(default=None, max_length=100),
    from_ts: datetime | None = Query(default=None, alias="from"),
    to_ts: datetime | None = Query(default=None, alias="to"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: SessionUser = Depends(_ALLOWED),
) -> AuditEntryListResponse:
    async with tenant_session(current_user.tenant_id) as session:
        stmt = select(AuditLogEntry)
        if actor_id is not None:
            stmt = stmt.where(AuditLogEntry.actor_id == actor_id)
        if event_type is not None:
            stmt = stmt.where(AuditLogEntry.event_type == event_type)
        if from_ts is not None:
            stmt = stmt.where(AuditLogEntry.timestamp >= from_ts)
        if to_ts is not None:
            stmt = stmt.where(AuditLogEntry.timestamp <= to_ts)
        stmt = stmt.order_by(AuditLogEntry.sequence.desc()).limit(limit).offset(offset)
        rows = (await session.execute(stmt)).scalars().all()
    return AuditEntryListResponse(
        entries=tuple(
            AuditEntryItem(
                id=r.id,
                sequence=r.sequence,
                actor_id=r.actor_id,
                event_type=r.event_type,
                details=r.details,
                timestamp=r.timestamp,
                entry_hash=r.entry_hash,
            )
            for r in rows
        )
    )
