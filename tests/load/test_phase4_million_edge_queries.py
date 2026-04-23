# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import random
import time
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from shared.graph.edges import ContactEdgeRepository

pytestmark = [pytest.mark.load, pytest.mark.asyncio]

_BATCH_SIZE = 1000
_AGE_BANDS = ("under_13", "13_15", "16_17", "18_plus")


async def _seed_tenant(engine: AsyncEngine, tenant_id: UUID) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) VALUES (:t, 'load', 'free', '{}', 30, "
                "'{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"t": str(tenant_id)},
        )


async def _seed_edges(engine: AsyncEngine, total: int, tenant_id: UUID, source_id: UUID) -> None:
    factory = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    now = datetime.now(UTC)
    rng = random.Random(42)
    for batch_start in range(0, total, _BATCH_SIZE):
        async with factory() as session, session.begin():
            await session.execute(
                text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)}
            )
            repo = ContactEdgeRepository(session)
            for _ in range(min(_BATCH_SIZE, total - batch_start)):
                target = uuid4()
                band = _AGE_BANDS[rng.randrange(len(_AGE_BANDS))]
                await repo.record_interaction(
                    tenant_id=tenant_id,
                    source_actor_id=source_id,
                    target_actor_id=target,
                    occurred_at=now - timedelta(days=rng.randrange(7)),
                    target_age_band=band,
                )


async def test_million_edge_graph_queries_under_500ms(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant = uuid4()
    source = uuid4()
    await _seed_tenant(admin_engine, tenant)
    await _seed_edges(admin_engine, 1_000_000, tenant, source)

    factory = async_sessionmaker(bind=admin_engine, expire_on_commit=False, autoflush=False)
    durations_ms: list[float] = []
    for _ in range(20):
        async with factory() as session, session.begin():
            await session.execute(
                text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant)}
            )
            repo = ContactEdgeRepository(session)
            start = time.perf_counter()
            view = await repo.get_contact_graph(
                tenant_id=tenant, actor_id=source, now=datetime.now(UTC), lookback_days=7
            )
            durations_ms.append((time.perf_counter() - start) * 1000.0)
            assert view.distinct_contacts_total > 0

    durations_ms.sort()
    p99 = durations_ms[int(0.99 * len(durations_ms))]
    assert p99 < 500.0, f"p99 was {p99:.1f}ms"
