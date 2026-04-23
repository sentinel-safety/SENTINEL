# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update

from services.dashboard_bff.app.dependencies import require_roles
from services.dashboard_bff.app.schemas import (
    DashboardRole,
    HoneypotEvidenceDetailResponse,
    HoneypotEvidenceListItem,
    HoneypotEvidenceListResponse,
    HoneypotToggleRequest,
    SessionUser,
)
from shared.db.models import HoneypotEvidencePackage, Tenant
from shared.db.session import tenant_session

router = APIRouter(prefix="/dashboard/api", tags=["honeypot"])

_ADMIN = require_roles(DashboardRole.ADMIN)
_ADMIN_OR_AUDITOR = require_roles(DashboardRole.ADMIN, DashboardRole.AUDITOR)


@router.put("/tenant/honeypot")
async def toggle_honeypot(
    payload: HoneypotToggleRequest, current_user: SessionUser = Depends(_ADMIN)
) -> dict[str, bool]:
    if payload.honeypot_enabled and not payload.legal_review_acknowledged:
        raise HTTPException(
            status_code=400,
            detail="legal_review_acknowledged must be true to enable honeypot",
        )
    async with tenant_session(current_user.tenant_id) as session:
        tenant = (
            await session.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
        ).scalar_one()
        flags = dict(tenant.feature_flags or {})
        flags["honeypot_enabled"] = bool(payload.honeypot_enabled)
        flags["honeypot_legal_review_acknowledged"] = bool(payload.legal_review_acknowledged)
        await session.execute(
            update(Tenant).where(Tenant.id == current_user.tenant_id).values(feature_flags=flags)
        )
    return {
        "honeypot_enabled": payload.honeypot_enabled,
        "legal_review_acknowledged": payload.legal_review_acknowledged,
    }


@router.get("/honeypot/evidence", response_model=HoneypotEvidenceListResponse)
async def list_evidence(
    current_user: SessionUser = Depends(_ADMIN_OR_AUDITOR),
) -> HoneypotEvidenceListResponse:
    async with tenant_session(current_user.tenant_id) as session:
        rows = (
            (
                await session.execute(
                    select(HoneypotEvidencePackage).order_by(
                        HoneypotEvidencePackage.created_at.desc()
                    )
                )
            )
            .scalars()
            .all()
        )
    return HoneypotEvidenceListResponse(
        evidence=tuple(
            HoneypotEvidenceListItem(
                id=r.id,
                actor_id=r.actor_id,
                persona_id=r.persona_id,
                content_hash=r.content_hash,
                created_at=r.created_at,
            )
            for r in rows
        )
    )


@router.get(
    "/honeypot/evidence/{evidence_id}",
    response_model=HoneypotEvidenceDetailResponse,
)
async def get_evidence_detail(
    evidence_id: UUID, current_user: SessionUser = Depends(_ADMIN_OR_AUDITOR)
) -> HoneypotEvidenceDetailResponse:
    async with tenant_session(current_user.tenant_id) as session:
        row = (
            await session.execute(
                select(HoneypotEvidencePackage).where(HoneypotEvidencePackage.id == evidence_id)
            )
        ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="evidence package not found")
    payload = dict(row.json_payload or {})
    return HoneypotEvidenceDetailResponse(
        id=row.id,
        actor_id=row.actor_id,
        persona_id=row.persona_id,
        content_hash=row.content_hash,
        created_at=row.created_at,
        synthetic_persona=bool(payload.get("synthetic_persona", True)),
        json_payload=payload,
    )
