# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from services.dashboard_bff.app.dependencies import get_current_user
from services.dashboard_bff.app.schemas import (
    DashboardRole,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    SessionUser,
    UserResponse,
)
from services.dashboard_bff.app.user_repository import get_by_id, update_last_login
from shared.auth.jwt import TokenError, decode_token, issue_token
from shared.auth.keys import load_keypair
from shared.auth.passwords import build_hasher, verify_password
from shared.config import Settings
from shared.db.models import DashboardUser
from shared.db.session import tenant_session

router = APIRouter(prefix="/dashboard/api/auth", tags=["auth"])


def _get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


def _issue_pair(
    *,
    user_id: UUID,
    tenant_id: UUID,
    role: DashboardRole,
    settings: Settings,
) -> tuple[str, str]:
    priv, _ = load_keypair(settings)
    now = datetime.now(UTC)
    access = issue_token(
        private_key_pem=priv,
        user_id=user_id,
        tenant_id=tenant_id,
        role=role.value,
        token_type="access",  # noqa: S106
        issued_at=now,
        expires_at=now + timedelta(minutes=settings.dashboard_access_token_ttl_minutes),
    )
    refresh = issue_token(
        private_key_pem=priv,
        user_id=user_id,
        tenant_id=tenant_id,
        role=role.value,
        token_type="refresh",  # noqa: S106
        issued_at=now,
        expires_at=now + timedelta(days=settings.dashboard_refresh_token_ttl_days),
    )
    return access, refresh


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, request: Request) -> LoginResponse:
    settings = _get_settings(request)
    hasher = build_hasher(
        time_cost=settings.dashboard_argon2_time_cost,
        memory_cost=settings.dashboard_argon2_memory_cost,
        parallelism=settings.dashboard_argon2_parallelism,
    )
    admin_dsn = settings.postgres_sync_dsn.replace("+psycopg", "+asyncpg")
    admin_engine = create_async_engine(admin_dsn, echo=False)
    try:
        async with admin_engine.connect() as conn:
            row = (
                await conn.execute(
                    select(DashboardUser).where(DashboardUser.email == payload.email)
                )
            ).one_or_none()
    finally:
        await admin_engine.dispose()
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    password_hash = row.password_hash
    if not verify_password(payload.password, password_hash, hasher=hasher):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    tenant_id = row.tenant_id
    user_id = row.id
    role = DashboardRole(row.role)
    display_name = row.display_name
    email = row.email
    async with tenant_session(tenant_id) as session:
        await update_last_login(session, user_id=user_id, now=datetime.now(UTC))
    access, refresh = _issue_pair(
        user_id=user_id, tenant_id=tenant_id, role=role, settings=settings
    )
    return LoginResponse(
        access_token=access,
        refresh_token=refresh,
        user=UserResponse(
            id=user_id,
            tenant_id=tenant_id,
            email=email,
            role=role,
            display_name=display_name,
            last_login_at=None,
        ),
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(payload: RefreshRequest, request: Request) -> RefreshResponse:
    settings = _get_settings(request)
    _, pub = load_keypair(settings)
    try:
        claims = decode_token(payload.refresh_token, public_key_pem=pub, expected_type="refresh")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid refresh token: {exc}",
        ) from exc
    priv, _ = load_keypair(settings)
    now = datetime.now(UTC)
    access = issue_token(
        private_key_pem=priv,
        user_id=claims.user_id,
        tenant_id=claims.tenant_id,
        role=claims.role,
        token_type="access",  # noqa: S106
        issued_at=now,
        expires_at=now + timedelta(minutes=settings.dashboard_access_token_ttl_minutes),
    )
    return RefreshResponse(access_token=access)


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: SessionUser = Depends(get_current_user),
) -> UserResponse:
    async with tenant_session(current_user.tenant_id) as session:
        row = await get_by_id(session, user_id=current_user.id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return UserResponse(
        id=row.id,
        tenant_id=row.tenant_id,
        email=row.email,
        role=DashboardRole(row.role),
        display_name=row.display_name,
        last_login_at=row.last_login_at,
    )
