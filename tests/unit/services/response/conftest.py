# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from shared.config import get_settings
from shared.db import reset_session_factories

_TABLES = (
    "audit_log_entry",
    "response_action",
    "score_history",
    "suspicion_profile",
    "pattern_match",
    "relationship_edge",
    "event",
    "conversation",
    "actor",
    "webhook_endpoint",
    "api_key",
    "tenant_action_config",
    "tenant",
)


@pytest.fixture(autouse=True)
def _reset_shared_db_caches() -> Iterator[None]:
    reset_session_factories()
    yield
    reset_session_factories()


def _admin_async_dsn() -> str:
    return get_settings().postgres_sync_dsn.replace("+psycopg", "+asyncpg")


@pytest.fixture
async def admin_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(_admin_async_dsn(), echo=False, pool_pre_ping=False)
    try:
        async with engine.connect():
            pass
    except Exception:
        await engine.dispose()
        pytest.skip("postgres unavailable")
    yield engine
    await engine.dispose()


@pytest.fixture
async def clean_tables(admin_engine: AsyncEngine) -> None:
    async with admin_engine.begin() as conn:
        for name in _TABLES:
            await conn.execute(text(f"TRUNCATE TABLE {name} CASCADE"))
