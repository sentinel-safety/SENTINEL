# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select, update
from sqlalchemy.engine import CursorResult

from services.dashboard_bff.app.dependencies import require_roles
from services.dashboard_bff.app.schemas import (
    ApiKeyCreateRequest,
    ApiKeyCreateResponse,
    ApiKeyListResponse,
    ApiKeySummary,
    DashboardRole,
    SessionUser,
    TenantActionConfigResponse,
    TenantSettings,
    WebhookCreateRequest,
    WebhookCreateResponse,
    WebhookListItem,
    WebhookListResponse,
)
from services.response.app.config_repository import load_or_create_config
from shared.db.models import ApiKey, Tenant, TenantActionConfig, WebhookEndpoint
from shared.db.session import tenant_session

router = APIRouter(prefix="/dashboard/api/tenant", tags=["tenant"])

_ADMIN = require_roles(DashboardRole.ADMIN)


def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


@router.get("/settings", response_model=TenantSettings)
async def get_tenant_settings(
    current_user: SessionUser = Depends(_ADMIN),
) -> TenantSettings:
    async with tenant_session(current_user.tenant_id) as session:
        row = (
            await session.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
        ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    return TenantSettings(
        name=row.name,
        tier=row.tier,
        compliance_jurisdictions=tuple(row.compliance_jurisdictions or ()),
        data_retention_days=row.data_retention_days,
    )


@router.put("/settings", response_model=TenantSettings)
async def put_tenant_settings(
    payload: TenantSettings, current_user: SessionUser = Depends(_ADMIN)
) -> TenantSettings:
    async with tenant_session(current_user.tenant_id) as session:
        await session.execute(
            update(Tenant)
            .where(Tenant.id == current_user.tenant_id)
            .values(
                name=payload.name,
                tier=payload.tier,
                compliance_jurisdictions=list(payload.compliance_jurisdictions),
                data_retention_days=payload.data_retention_days,
            )
        )
    return payload


@router.get("/action-config", response_model=TenantActionConfigResponse)
async def get_action_config(
    current_user: SessionUser = Depends(_ADMIN),
) -> TenantActionConfigResponse:
    async with tenant_session(current_user.tenant_id) as session:
        config = await load_or_create_config(session, tenant_id=current_user.tenant_id)
    return TenantActionConfigResponse(
        mode=config.mode.value, action_overrides=dict(config.action_overrides)
    )


@router.put("/action-config", response_model=TenantActionConfigResponse)
async def put_action_config(
    payload: TenantActionConfigResponse,
    current_user: SessionUser = Depends(_ADMIN),
) -> TenantActionConfigResponse:
    async with tenant_session(current_user.tenant_id) as session:
        await load_or_create_config(session, tenant_id=current_user.tenant_id)
        await session.execute(
            update(TenantActionConfig)
            .where(TenantActionConfig.tenant_id == current_user.tenant_id)
            .values(
                mode=payload.mode,
                action_overrides={k: list(v) for k, v in payload.action_overrides.items()},
                updated_at=datetime.now(UTC),
            )
        )
    return payload


@router.get("/webhooks", response_model=WebhookListResponse)
async def list_webhooks(
    current_user: SessionUser = Depends(_ADMIN),
) -> WebhookListResponse:
    async with tenant_session(current_user.tenant_id) as session:
        rows = (
            (
                await session.execute(
                    select(WebhookEndpoint).order_by(WebhookEndpoint.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
    return WebhookListResponse(
        webhooks=tuple(
            WebhookListItem(
                id=r.id,
                url=r.url,
                events=tuple(r.subscribed_topics),
                active=r.active,
                created_at=r.created_at,
            )
            for r in rows
        )
    )


@router.post(
    "/webhooks",
    response_model=WebhookCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_webhook(
    payload: WebhookCreateRequest, current_user: SessionUser = Depends(_ADMIN)
) -> WebhookCreateResponse:
    secret = secrets.token_urlsafe(32)
    async with tenant_session(current_user.tenant_id) as session:
        row = WebhookEndpoint(
            tenant_id=current_user.tenant_id,
            url=payload.url,
            secret_hash=_sha256_hex(secret),
            subscribed_topics=list(payload.events),
            active=True,
        )
        session.add(row)
        await session.flush()
        item = WebhookListItem(
            id=row.id,
            url=row.url,
            events=tuple(row.subscribed_topics),
            active=row.active,
            created_at=row.created_at,
        )
    return WebhookCreateResponse(webhook=item, secret=secret)


@router.delete("/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(webhook_id: UUID, current_user: SessionUser = Depends(_ADMIN)) -> Response:
    async with tenant_session(current_user.tenant_id) as session:
        result = cast(
            CursorResult[tuple[()]],
            await session.execute(delete(WebhookEndpoint).where(WebhookEndpoint.id == webhook_id)),
        )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="webhook not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/api-keys", response_model=ApiKeyListResponse)
async def list_api_keys(
    current_user: SessionUser = Depends(_ADMIN),
) -> ApiKeyListResponse:
    async with tenant_session(current_user.tenant_id) as session:
        rows = (
            (await session.execute(select(ApiKey).order_by(ApiKey.created_at.desc())))
            .scalars()
            .all()
        )
    return ApiKeyListResponse(
        api_keys=tuple(
            ApiKeySummary(
                id=r.id,
                name=r.name,
                prefix=r.key_prefix,
                scope=r.scope,
                created_at=r.created_at,
                revoked_at=r.revoked_at,
                last_used_at=r.last_used_at,
            )
            for r in rows
        )
    )


@router.post(
    "/api-keys",
    response_model=ApiKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    payload: ApiKeyCreateRequest, current_user: SessionUser = Depends(_ADMIN)
) -> ApiKeyCreateResponse:
    raw = secrets.token_urlsafe(32)
    prefix = f"sk_{secrets.token_hex(4)}"
    full_secret = f"{prefix}.{raw}"
    key_hash = _sha256_hex(full_secret)
    async with tenant_session(current_user.tenant_id) as session:
        row = ApiKey(
            tenant_id=current_user.tenant_id,
            name=payload.name,
            key_hash=key_hash,
            key_prefix=prefix,
            scope=payload.scope,
        )
        session.add(row)
        await session.flush()
        summary = ApiKeySummary(
            id=row.id,
            name=row.name,
            prefix=row.key_prefix,
            scope=row.scope,
            created_at=row.created_at,
            revoked_at=None,
            last_used_at=None,
        )
    return ApiKeyCreateResponse(api_key=summary, secret=full_secret)


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(key_id: UUID, current_user: SessionUser = Depends(_ADMIN)) -> Response:
    async with tenant_session(current_user.tenant_id) as session:
        result = cast(
            CursorResult[tuple[()]],
            await session.execute(delete(ApiKey).where(ApiKey.id == key_id)),
        )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="api key not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
