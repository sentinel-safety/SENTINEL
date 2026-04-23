# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import secrets
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models import TenantActionConfig as TenantActionConfigRow
from shared.schemas.enums import ActionMode
from shared.schemas.tenant_action_config import TenantActionConfig


async def load_or_create_config(session: AsyncSession, *, tenant_id: UUID) -> TenantActionConfig:
    stmt = select(TenantActionConfigRow).where(TenantActionConfigRow.tenant_id == tenant_id)
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is not None:
        return TenantActionConfig(
            tenant_id=row.tenant_id,
            mode=ActionMode(row.mode),
            action_overrides={k: tuple(v) for k, v in (row.action_overrides or {}).items()},
            webhook_secret=row.webhook_secret_hash,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
    now = datetime.now(UTC)
    secret = secrets.token_hex(32)
    insert = (
        pg_insert(TenantActionConfigRow)
        .values(
            tenant_id=tenant_id,
            mode=ActionMode.ADVISORY.value,
            action_overrides={},
            webhook_secret_hash=secret,
            created_at=now,
            updated_at=now,
        )
        .on_conflict_do_nothing(index_elements=[TenantActionConfigRow.tenant_id])
    )
    await session.execute(insert)
    await session.commit()
    return TenantActionConfig(
        tenant_id=tenant_id,
        mode=ActionMode.ADVISORY,
        action_overrides={},
        webhook_secret=secret,
        created_at=now,
        updated_at=now,
    )
