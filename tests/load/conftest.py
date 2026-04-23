# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from shared.config import get_settings
from shared.db import reset_session_factories


@pytest.fixture(autouse=True)
def _ingestion_auth_bypass_for_load_tests() -> Iterator[None]:
    prior = os.environ.get("SENTINEL_INGESTION_AUTH_TEST_BYPASS")
    os.environ["SENTINEL_INGESTION_AUTH_TEST_BYPASS"] = "1"
    yield
    if prior is None:
        os.environ.pop("SENTINEL_INGESTION_AUTH_TEST_BYPASS", None)
    else:
        os.environ["SENTINEL_INGESTION_AUTH_TEST_BYPASS"] = prior


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
    engine = create_async_engine(_admin_async_dsn(), echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture
async def clean_tables(admin_engine: AsyncEngine) -> None:
    async with admin_engine.begin() as conn:
        for name in _TABLES:
            await conn.execute(text(f"TRUNCATE TABLE {name} CASCADE"))
