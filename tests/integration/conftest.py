# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from shared.config import get_settings
from shared.db import reset_session_factories
from shared.vector.qdrant_client import get_qdrant_client

_TABLES = (
    "bug_report",
    "synthetic_conversation",
    "synthetic_run",
    "federation_reputation_event",
    "federation_signal",
    "federation_tenant_secret",
    "federation_publisher",
    "honeypot_activation_log",
    "honeypot_evidence_package",
    "audit_log_entry",
    "dashboard_user",
    "reasoning",
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
    get_qdrant_client.cache_clear()
    yield
    reset_session_factories()


@pytest.fixture(autouse=True)
def _ingestion_auth_bypass_for_tests(request: pytest.FixtureRequest) -> Iterator[None]:
    """Toggle the env-gated bypass for /v1/events auth so legacy integration
    tests keep working. Tests that exercise real auth opt out with the
    `no_ingestion_auth_bypass` marker."""
    import os

    if "no_ingestion_auth_bypass" in request.keywords:
        os.environ.pop("SENTINEL_INGESTION_AUTH_TEST_BYPASS", None)
        yield
        return
    prior = os.environ.get("SENTINEL_INGESTION_AUTH_TEST_BYPASS")
    os.environ["SENTINEL_INGESTION_AUTH_TEST_BYPASS"] = "1"
    yield
    if prior is None:
        os.environ.pop("SENTINEL_INGESTION_AUTH_TEST_BYPASS", None)
    else:
        os.environ["SENTINEL_INGESTION_AUTH_TEST_BYPASS"] = prior
    get_qdrant_client.cache_clear()


def _admin_async_dsn() -> str:
    return get_settings().postgres_sync_dsn.replace("+psycopg", "+asyncpg")


@pytest.fixture
async def admin_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(_admin_async_dsn(), echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture
async def app_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(get_settings().postgres_dsn, echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture
async def session_factory(app_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=app_engine, expire_on_commit=False, autoflush=False)


@pytest.fixture
async def clean_tables(admin_engine: AsyncEngine) -> None:
    async with admin_engine.begin() as conn:
        for name in _TABLES:
            await conn.execute(text(f"TRUNCATE TABLE {name} CASCADE"))
