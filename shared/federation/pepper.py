# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import hashlib
import os
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models import FederationTenantSecret


def hash_actor(*, actor_id: UUID, pepper: bytes) -> bytes:
    return hashlib.sha256(actor_id.bytes + pepper).digest()


async def load_or_create_tenant_secret(
    session: AsyncSession,
    *,
    tenant_id: UUID,
) -> FederationTenantSecret:
    from sqlalchemy import select

    result = await session.execute(
        select(FederationTenantSecret).where(FederationTenantSecret.tenant_id == tenant_id)
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        return existing
    record = FederationTenantSecret(
        tenant_id=tenant_id,
        hmac_secret=os.urandom(32),
        actor_pepper=os.urandom(32),
    )
    session.add(record)
    await session.flush()
    return record
