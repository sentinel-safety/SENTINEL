# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from shared.graph.edges import ContactEdgeRepository

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _open(engine: AsyncEngine, tenant_id):  # type: ignore[no-untyped-def]
    factory = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    s = factory()
    await s.begin()
    await s.execute(text("SELECT set_config('app.tenant_id', :t, true)"), {"t": str(tenant_id)})
    return s


async def test_get_contact_graph_only_returns_current_tenant_edges(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_a = uuid4()
    tenant_b = uuid4()
    shared_actor = uuid4()
    now = datetime.now(UTC)

    s = await _open(admin_engine, tenant_a)
    try:
        await ContactEdgeRepository(s).record_interaction(
            tenant_id=tenant_a,
            source_actor_id=shared_actor,
            target_actor_id=uuid4(),
            occurred_at=now,
            target_age_band="under_13",
        )
        await s.commit()
    finally:
        await s.close()

    s = await _open(admin_engine, tenant_b)
    try:
        await ContactEdgeRepository(s).record_interaction(
            tenant_id=tenant_b,
            source_actor_id=shared_actor,
            target_actor_id=uuid4(),
            occurred_at=now,
            target_age_band="13_15",
        )
        await ContactEdgeRepository(s).record_interaction(
            tenant_id=tenant_b,
            source_actor_id=shared_actor,
            target_actor_id=uuid4(),
            occurred_at=now,
            target_age_band="13_15",
        )
        await s.commit()
    finally:
        await s.close()

    s = await _open(admin_engine, tenant_a)
    try:
        view_a = await ContactEdgeRepository(s).get_contact_graph(
            tenant_id=tenant_a, actor_id=shared_actor, now=now, lookback_days=7
        )
    finally:
        await s.close()

    assert view_a.distinct_contacts_total == 1
    assert view_a.distinct_minor_contacts_window == 1
