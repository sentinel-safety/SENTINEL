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
    FalseSignalRequest,
    FederationSettingsResponse,
    FederationToggleRequest,
    PublisherListResponse,
    PublisherSnapshot,
    SessionUser,
)
from shared.db.models import FederationPublisher, Tenant
from shared.db.session import tenant_session
from shared.federation.publisher_repository import list_publishers, update_reputation
from shared.federation.reputation import ReputationDelta, adjust_reputation
from shared.federation.reputation_repository import insert_reputation_event

router = APIRouter(prefix="/dashboard/api", tags=["federation"])

_ADMIN = require_roles(DashboardRole.ADMIN)
_ADMIN_OR_AUDITOR = require_roles(DashboardRole.ADMIN, DashboardRole.AUDITOR)


@router.put("/tenant/federation", response_model=FederationSettingsResponse)
async def put_federation_settings(
    payload: FederationToggleRequest,
    current_user: SessionUser = Depends(_ADMIN),
) -> FederationSettingsResponse:
    if payload.enabled and not payload.federation_acknowledgment:
        raise HTTPException(
            status_code=400,
            detail="federation_acknowledgment must be true to enable federation",
        )
    async with tenant_session(current_user.tenant_id) as session:
        tenant = (
            await session.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
        ).scalar_one()
        flags = dict(tenant.feature_flags or {})
        flags["federation_enabled"] = payload.enabled
        flags["federation_publish"] = payload.publish
        flags["federation_subscribe"] = payload.subscribe
        flags["federation_jurisdictions_filter"] = payload.jurisdictions_filter
        await session.execute(
            update(Tenant).where(Tenant.id == current_user.tenant_id).values(feature_flags=flags)
        )
    return FederationSettingsResponse(
        enabled=payload.enabled,
        publish=payload.publish,
        subscribe=payload.subscribe,
        jurisdictions_filter=payload.jurisdictions_filter,
    )


@router.get("/tenant/federation", response_model=FederationSettingsResponse)
async def get_federation_settings(
    current_user: SessionUser = Depends(_ADMIN),
) -> FederationSettingsResponse:
    async with tenant_session(current_user.tenant_id) as session:
        tenant = (
            await session.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
        ).scalar_one_or_none()
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    flags = dict(tenant.feature_flags or {})
    return FederationSettingsResponse(
        enabled=bool(flags.get("federation_enabled", False)),
        publish=bool(flags.get("federation_publish", False)),
        subscribe=bool(flags.get("federation_subscribe", False)),
        jurisdictions_filter=list(flags.get("federation_jurisdictions_filter", [])),
    )


@router.get("/federation/publishers", response_model=PublisherListResponse)
async def list_federation_publishers(
    current_user: SessionUser = Depends(_ADMIN_OR_AUDITOR),
) -> PublisherListResponse:
    async with tenant_session(current_user.tenant_id) as session:
        publishers = await list_publishers(session)
    return PublisherListResponse(
        publishers=tuple(
            PublisherSnapshot(
                tenant_id=p.tenant_id,
                display_name=p.display_name,
                reputation=p.reputation,
                jurisdictions=list(p.jurisdictions or []),
                revoked=p.revoked_at is not None,
            )
            for p in publishers
        )
    )


@router.post("/federation/false-signal", status_code=200)
async def report_false_signal(
    payload: FalseSignalRequest,
    current_user: SessionUser = Depends(_ADMIN),
) -> dict[str, str]:
    async with tenant_session(current_user.tenant_id) as session:
        from shared.db.models import FederationSignal as FederationSignalModel

        signal_row = (
            await session.execute(
                select(FederationSignalModel).where(FederationSignalModel.id == payload.signal_id)
            )
        ).scalar_one_or_none()
        if signal_row is None:
            raise HTTPException(status_code=404, detail="signal not found")

        publisher_id: UUID = signal_row.publisher_tenant_id

        publisher = (
            await session.execute(
                select(FederationPublisher).where(FederationPublisher.tenant_id == publisher_id)
            )
        ).scalar_one_or_none()
        if publisher is None:
            raise HTTPException(status_code=404, detail="publisher not found")

        new_rep = adjust_reputation(publisher.reputation, ReputationDelta.EXPLICIT_COMPLAINT.name)
        await update_reputation(session, tenant_id=publisher_id, reputation=new_rep)
        await insert_reputation_event(
            session,
            publisher_tenant_id=publisher_id,
            reporter_tenant_id=current_user.tenant_id,
            delta=ReputationDelta.EXPLICIT_COMPLAINT,
            reason=payload.reason[:100],
        )
    return {"status": "recorded"}
