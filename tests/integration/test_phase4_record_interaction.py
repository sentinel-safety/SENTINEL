# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from shared.graph.edges import ContactEdgeRepository

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _session(engine: AsyncEngine, tenant_id):  # type: ignore[no-untyped-def]
    factory = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    session = factory()
    await session.begin()
    await session.execute(
        text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)}
    )
    return session


async def test_record_interaction_creates_vertices_and_edge(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    source = uuid4()
    target = uuid4()
    now = datetime.now(UTC)
    session = await _session(admin_engine, tenant_id)
    try:
        repo = ContactEdgeRepository(session)
        await repo.record_interaction(
            tenant_id=tenant_id,
            source_actor_id=source,
            target_actor_id=target,
            occurred_at=now,
            target_age_band="under_13",
        )
        await session.commit()
    finally:
        await session.close()

    session = await _session(admin_engine, tenant_id)
    try:
        async with session.begin_nested():
            await session.execute(text("SET search_path = ag_catalog, public"))
            row = await session.execute(
                text(
                    "SELECT count(*) FROM ag_catalog.cypher('sentinel_graph', "
                    "$$ MATCH (a:Actor)-[r:INTERACTED_WITH]->(b:Actor) "
                    "WHERE a.tenant_id = '" + str(tenant_id) + "' "
                    "RETURN count(r) AS n $$) AS (n agtype)"
                )
            )
            count_str = str(row.scalar_one())
            assert count_str.strip('"') == "1"
    finally:
        await session.close()


async def test_record_interaction_idempotent_updates_count(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    source = uuid4()
    target = uuid4()
    base = datetime.now(UTC)
    session = await _session(admin_engine, tenant_id)
    try:
        repo = ContactEdgeRepository(session)
        for i in range(3):
            await repo.record_interaction(
                tenant_id=tenant_id,
                source_actor_id=source,
                target_actor_id=target,
                occurred_at=base + timedelta(minutes=i),
                target_age_band="13_15",
            )
        await session.commit()
    finally:
        await session.close()

    session = await _session(admin_engine, tenant_id)
    try:
        await session.execute(text("SET search_path = ag_catalog, public"))
        row = await session.execute(
            text(
                "SELECT * FROM ag_catalog.cypher('sentinel_graph', "
                "$$ MATCH (a:Actor {actor_id: '" + str(source) + "'})-[r:INTERACTED_WITH]->"
                "(b:Actor {actor_id: '" + str(target) + "'}) "
                "RETURN r.count $$) AS (c agtype)"
            )
        )
        c = str(row.scalar_one())
        assert c.strip('"').strip() == "3"
    finally:
        await session.close()
