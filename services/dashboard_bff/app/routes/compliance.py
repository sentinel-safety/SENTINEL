# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import Field
from sqlalchemy import CursorResult, delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from services.dashboard_bff.app.dependencies import require_roles
from services.dashboard_bff.app.export_builder import build_export_zip
from services.dashboard_bff.app.schemas import (
    ComplianceExportRequest,
    DashboardRole,
    SessionUser,
)
from shared.audit.chain import append_entry
from shared.db.models import (
    Actor,
    AuditLogEntry,
    Event,
    PatternMatch,
    Reasoning,
    ResponseAction,
    SuspicionProfile,
)
from shared.db.session import tenant_session
from shared.schemas.audit_log import AuditEventType
from shared.schemas.base import FrozenModel

router = APIRouter(prefix="/dashboard/api/compliance", tags=["compliance"])

_ALLOWED = require_roles(DashboardRole.ADMIN, DashboardRole.AUDITOR)
_VALID_CATEGORIES = {"audit_log", "suspicion_profiles"}


async def _fetch_audit(
    session: AsyncSession, *, frm: datetime, to: datetime
) -> list[dict[str, Any]]:
    stmt = (
        select(AuditLogEntry)
        .where(AuditLogEntry.timestamp >= frm, AuditLogEntry.timestamp <= to)
        .order_by(AuditLogEntry.sequence.asc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": str(r.id),
            "sequence": r.sequence,
            "event_type": r.event_type,
            "actor_id": str(r.actor_id) if r.actor_id else "",
            "timestamp": r.timestamp.isoformat(),
            "entry_hash": r.entry_hash,
        }
        for r in rows
    ]


async def _fetch_profiles(session: AsyncSession) -> list[dict[str, Any]]:
    rows = (await session.execute(select(SuspicionProfile))).scalars().all()
    return [
        {
            "actor_id": str(r.actor_id),
            "current_score": r.current_score,
            "tier": r.tier,
            "tier_entered_at": r.tier_entered_at.isoformat(),
        }
        for r in rows
    ]


@router.post("/export")
async def export_compliance(
    payload: ComplianceExportRequest,
    current_user: SessionUser = Depends(_ALLOWED),
) -> StreamingResponse:
    unknown = set(payload.categories) - _VALID_CATEGORIES
    if unknown:
        raise HTTPException(status_code=400, detail=f"unknown categories: {sorted(unknown)}")
    data: dict[str, list[dict[str, Any]]] = {}
    async with tenant_session(current_user.tenant_id) as session:
        for cat in payload.categories:
            if cat == "audit_log":
                data[cat] = await _fetch_audit(session, frm=payload.from_date, to=payload.to_date)
            elif cat == "suspicion_profiles":
                data[cat] = await _fetch_profiles(session)
        await append_entry(
            session,
            tenant_id=current_user.tenant_id,
            event_type=AuditEventType.COMPLIANCE_EXPORTED.value,
            timestamp=datetime.now(UTC),
            details={
                "user_id": str(current_user.id),
                "role": current_user.role.value,
                "categories": list(payload.categories),
                "from": payload.from_date.isoformat(),
                "to": payload.to_date.isoformat(),
            },
        )
    zip_bytes = build_export_zip(data)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    filename = f"compliance_export_{stamp}.zip"

    def _iter() -> Iterator[bytes]:
        yield zip_bytes

    return StreamingResponse(
        _iter(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class GdprErasureRequest(FrozenModel):
    actor_id: UUID
    requester_email: str = Field(min_length=3, max_length=320)
    request_reference: str = Field(default="", max_length=200)


class GdprErasureResponse(FrozenModel):
    actor_id: UUID
    events_removed: int
    pattern_matches_removed: int
    reasoning_removed: int
    response_actions_removed: int
    suspicion_profile_removed: bool
    audit_entries_pseudonymised: int
    erased_at: datetime


_ADMIN_ONLY = require_roles(DashboardRole.ADMIN)


async def _delete_scoped(session: AsyncSession, model: Any, tenant_id: UUID, actor_id: UUID) -> int:
    result = await session.execute(
        delete(model).where(model.tenant_id == tenant_id, model.actor_id == actor_id)
    )
    assert isinstance(result, CursorResult)
    return int(result.rowcount or 0)


@router.post("/gdpr/erasure", response_model=GdprErasureResponse)
async def gdpr_erasure(
    payload: GdprErasureRequest,
    current_user: SessionUser = Depends(_ADMIN_ONLY),
) -> GdprErasureResponse:
    """GDPR Article 17 "Right to erasure" execution for a single actor.

    Removes PII-bearing rows (events, pattern_matches, reasoning, response_actions,
    suspicion_profile) and pseudonymises audit_log_entry rows (preserves the
    hash chain per §7 of the spec).
    """
    now = datetime.now(UTC)
    async with tenant_session(current_user.tenant_id) as session:
        actor_row = (
            await session.execute(
                select(Actor).where(
                    Actor.tenant_id == current_user.tenant_id,
                    Actor.id == payload.actor_id,
                )
            )
        ).scalar_one_or_none()
        if actor_row is None:
            raise HTTPException(status_code=404, detail="actor not found in tenant")

        events_removed = await _delete_scoped(
            session, Event, current_user.tenant_id, payload.actor_id
        )
        pattern_removed = await _delete_scoped(
            session, PatternMatch, current_user.tenant_id, payload.actor_id
        )
        reasoning_removed = await _delete_scoped(
            session, Reasoning, current_user.tenant_id, payload.actor_id
        )
        actions_removed = await _delete_scoped(
            session, ResponseAction, current_user.tenant_id, payload.actor_id
        )
        profile_result = await session.execute(
            delete(SuspicionProfile).where(
                SuspicionProfile.tenant_id == current_user.tenant_id,
                SuspicionProfile.actor_id == payload.actor_id,
            )
        )
        assert isinstance(profile_result, CursorResult)
        profile_removed = (profile_result.rowcount or 0) > 0

        audit_update = await session.execute(
            update(AuditLogEntry)
            .where(
                AuditLogEntry.tenant_id == current_user.tenant_id,
                AuditLogEntry.actor_id == payload.actor_id,
            )
            .values(actor_id=None)
        )
        assert isinstance(audit_update, CursorResult)
        audit_pseudonymised = int(audit_update.rowcount or 0)

        await session.execute(
            delete(Actor).where(
                Actor.tenant_id == current_user.tenant_id, Actor.id == payload.actor_id
            )
        )

        await append_entry(
            session,
            tenant_id=current_user.tenant_id,
            event_type=AuditEventType.ACTOR_ERASED.value,
            timestamp=now,
            details={
                "actor_id": str(payload.actor_id),
                "requester_email": payload.requester_email,
                "request_reference": payload.request_reference,
                "operator_user_id": str(current_user.id),
                "events_removed": events_removed,
                "pattern_matches_removed": pattern_removed,
                "reasoning_removed": reasoning_removed,
                "response_actions_removed": actions_removed,
                "suspicion_profile_removed": profile_removed,
                "audit_entries_pseudonymised": audit_pseudonymised,
            },
        )

    return GdprErasureResponse(
        actor_id=payload.actor_id,
        events_removed=events_removed,
        pattern_matches_removed=pattern_removed,
        reasoning_removed=reasoning_removed,
        response_actions_removed=actions_removed,
        suspicion_profile_removed=profile_removed,
        audit_entries_pseudonymised=audit_pseudonymised,
        erased_at=now,
    )
