# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models import FederationPublisher


async def register_publisher(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    display_name: str,
    hmac_secret: bytes,
    jurisdictions: list[str] | None = None,
) -> FederationPublisher:
    publisher = FederationPublisher(
        tenant_id=tenant_id,
        display_name=display_name,
        hmac_secret=hmac_secret,
        jurisdictions=jurisdictions or [],
        reputation=50,
    )
    session.add(publisher)
    await session.flush()
    return publisher


async def get_publisher(
    session: AsyncSession,
    *,
    tenant_id: UUID,
) -> FederationPublisher | None:
    result = await session.execute(
        select(FederationPublisher).where(FederationPublisher.tenant_id == tenant_id)
    )
    return result.scalar_one_or_none()


async def update_reputation(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    reputation: int,
) -> None:
    await session.execute(
        update(FederationPublisher)
        .where(FederationPublisher.tenant_id == tenant_id)
        .values(reputation=reputation)
    )


async def list_publishers(session: AsyncSession) -> tuple[FederationPublisher, ...]:
    result = await session.execute(
        select(FederationPublisher).where(FederationPublisher.revoked_at.is_(None))
    )
    return tuple(result.scalars().all())


async def revoke_publisher(
    session: AsyncSession,
    *,
    tenant_id: UUID,
) -> None:
    await session.execute(
        update(FederationPublisher)
        .where(FederationPublisher.tenant_id == tenant_id)
        .values(revoked_at=datetime.now(UTC))
    )
