# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import hashlib
import hmac
from datetime import UTC, datetime
from uuid import UUID

from pydantic import Field
from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import create_async_engine

from shared.config import get_settings
from shared.db.models import ApiKey as ApiKeyRow
from shared.schemas.base import FrozenModel, UtcDatetime


class ResolvedApiKey(FrozenModel):
    id: UUID
    tenant_id: UUID
    scope: str = Field(min_length=1, max_length=16)
    prefix: str
    last_used_at: UtcDatetime | None = None


def hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _admin_async_dsn() -> str:
    return get_settings().postgres_sync_dsn.replace("+psycopg", "+asyncpg")


async def resolve_api_key(raw_secret: str) -> ResolvedApiKey | None:
    """Lookup an API key by its full bearer token. Returns None if missing/revoked/expired.

    Runs against the superuser DSN because the api_key row is RLS-scoped on tenant_id
    and the caller's tenant_id is not known until the key resolves.
    """
    if not raw_secret or "." not in raw_secret:
        return None
    expected_hash = hash_api_key(raw_secret)
    engine = create_async_engine(_admin_async_dsn())
    try:
        async with engine.begin() as conn:
            stmt = select(
                ApiKeyRow.id,
                ApiKeyRow.tenant_id,
                ApiKeyRow.scope,
                ApiKeyRow.key_prefix,
                ApiKeyRow.key_hash,
                ApiKeyRow.revoked_at,
                ApiKeyRow.expires_at,
                ApiKeyRow.last_used_at,
            )
            rows = (await conn.execute(stmt)).all()
        match: ResolvedApiKey | None = None
        for row in rows:
            if not hmac.compare_digest(row.key_hash, expected_hash):
                continue
            if row.revoked_at is not None:
                return None
            now = datetime.now(UTC)
            if row.expires_at is not None and row.expires_at < now:
                return None
            match = ResolvedApiKey(
                id=row.id,
                tenant_id=row.tenant_id,
                scope=row.scope,
                prefix=row.key_prefix,
                last_used_at=row.last_used_at,
            )
            break
        if match is not None:
            async with engine.begin() as conn:
                await conn.execute(
                    update(ApiKeyRow)
                    .where(ApiKeyRow.id == match.id)
                    .values(last_used_at=datetime.now(UTC))
                )
        return match
    finally:
        await engine.dispose()


async def touch_api_key(api_key_id: UUID) -> None:
    """Separate helper to bump last_used_at without re-resolving (used by background)."""
    engine = create_async_engine(_admin_async_dsn())
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text("UPDATE api_key SET last_used_at = now() WHERE id = :k"),
                {"k": str(api_key_id)},
            )
    finally:
        await engine.dispose()
