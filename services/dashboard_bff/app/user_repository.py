# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models import DashboardUser


async def get_by_email(
    session: AsyncSession, *, tenant_id: UUID, email: str
) -> DashboardUser | None:
    stmt = select(DashboardUser).where(
        DashboardUser.tenant_id == tenant_id,
        DashboardUser.email == email,
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def get_by_id(session: AsyncSession, *, user_id: UUID) -> DashboardUser | None:
    stmt = select(DashboardUser).where(DashboardUser.id == user_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    email: str,
    password_hash: str,
    role: str,
    display_name: str,
) -> DashboardUser:
    user = DashboardUser(
        tenant_id=tenant_id,
        email=email,
        password_hash=password_hash,
        role=role,
        display_name=display_name,
    )
    session.add(user)
    await session.flush()
    return user


async def update_last_login(session: AsyncSession, *, user_id: UUID, now: datetime) -> None:
    await session.execute(
        update(DashboardUser).where(DashboardUser.id == user_id).values(last_login_at=now)
    )
