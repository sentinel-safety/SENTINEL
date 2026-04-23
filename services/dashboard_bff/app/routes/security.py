# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select, update

from services.dashboard_bff.app.dependencies import require_roles
from services.dashboard_bff.app.schemas import (
    BugReportIn,
    BugReportListResponse,
    BugReportOut,
    BugReportPatch,
    DashboardRole,
    SessionUser,
)
from shared.db.models import BugReport
from shared.db.session import tenant_session

router = APIRouter(prefix="/dashboard/api/security", tags=["security"])

_ADMIN = require_roles(DashboardRole.ADMIN)
_ADMIN_OR_AUDITOR = require_roles(DashboardRole.ADMIN, DashboardRole.AUDITOR)


@router.post("/bug-reports", response_model=BugReportOut, status_code=201)
async def submit_bug_report(
    payload: BugReportIn,
    x_sentinel_tenant_id: UUID = Header(..., alias="X-Sentinel-Tenant-Id"),
) -> BugReportOut:
    async with tenant_session(x_sentinel_tenant_id) as session:
        row = BugReport(
            tenant_id=x_sentinel_tenant_id,
            reporter_email=payload.reporter_email,
            summary=payload.summary,
            details=payload.details,
            severity=payload.severity,
        )
        session.add(row)
        await session.flush()
        return BugReportOut(
            id=row.id,
            tenant_id=row.tenant_id,
            reporter_email=row.reporter_email,
            summary=row.summary,
            severity=row.severity,
            status=row.status,
            received_at=row.received_at,
            resolved_at=row.resolved_at,
        )


@router.get("/bug-reports", response_model=BugReportListResponse)
async def list_bug_reports(
    current_user: SessionUser = Depends(_ADMIN_OR_AUDITOR),
) -> BugReportListResponse:
    async with tenant_session(current_user.tenant_id) as session:
        rows = (
            (await session.execute(select(BugReport).order_by(BugReport.received_at.desc())))
            .scalars()
            .all()
        )
    return BugReportListResponse(
        reports=tuple(
            BugReportOut(
                id=r.id,
                tenant_id=r.tenant_id,
                reporter_email=r.reporter_email,
                summary=r.summary,
                severity=r.severity,
                status=r.status,
                received_at=r.received_at,
                resolved_at=r.resolved_at,
            )
            for r in rows
        )
    )


@router.patch("/bug-reports/{report_id}", response_model=BugReportOut)
async def update_bug_report(
    report_id: UUID,
    payload: BugReportPatch,
    current_user: SessionUser = Depends(_ADMIN),
) -> BugReportOut:
    async with tenant_session(current_user.tenant_id) as session:
        row = (
            await session.execute(select(BugReport).where(BugReport.id == report_id))
        ).scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="bug report not found")
        updates: dict[str, object] = {}
        if payload.status is not None:
            updates["status"] = payload.status
        if payload.status == "resolved" and row.resolved_at is None:
            updates["resolved_at"] = datetime.now(UTC)
        if updates:
            await session.execute(
                update(BugReport).where(BugReport.id == report_id).values(**updates)
            )
            await session.flush()
            row = (
                await session.execute(select(BugReport).where(BugReport.id == report_id))
            ).scalar_one()
        return BugReportOut(
            id=row.id,
            tenant_id=row.tenant_id,
            reporter_email=row.reporter_email,
            summary=row.summary,
            severity=row.severity,
            status=row.status,
            received_at=row.received_at,
            resolved_at=row.resolved_at,
        )
