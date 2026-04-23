# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models import FederationTenantSecret
from shared.federation.pepper import load_or_create_tenant_secret


async def get_or_create(
    session: AsyncSession,
    *,
    tenant_id: UUID,
) -> FederationTenantSecret:
    return await load_or_create_tenant_secret(session, tenant_id=tenant_id)
