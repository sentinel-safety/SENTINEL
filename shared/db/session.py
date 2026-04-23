# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from shared.config import get_settings

_SET_TENANT_SQL = text("SELECT set_config('app.tenant_id', :tid, true)")


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.postgres_dsn,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
        echo=False,
    )


@lru_cache(maxsize=1)
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=get_engine(),
        expire_on_commit=False,
        autoflush=False,
    )


@asynccontextmanager
async def tenant_session(tenant_id: UUID) -> AsyncIterator[AsyncSession]:
    """Open a session with RLS bound to the given tenant.

    Every query inside this block sees only rows where tenant_id matches.
    """
    factory = get_session_factory()
    async with factory() as session, session.begin():
        await session.execute(_SET_TENANT_SQL, {"tid": str(tenant_id)})
        yield session


def reset_session_factories() -> None:
    """Test helper: drops cached engine/factory so a new event loop can rebuild."""
    get_engine.cache_clear()
    get_session_factory.cache_clear()
