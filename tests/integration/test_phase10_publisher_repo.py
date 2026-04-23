# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from shared.federation.publisher_repository import (
    get_publisher,
    list_publishers,
    register_publisher,
    revoke_publisher,
    update_reputation,
)
from shared.federation.reputation_repository import (
    insert_reputation_event,
    list_events_for_publisher,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed_tenant(engine: AsyncEngine, tenant_id) -> None:  # type: ignore[no-untyped-def]
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) VALUES (:t, 'pub-test', 'free', '{}', 30, "
                "'{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"t": str(tenant_id)},
        )


@pytest.fixture
async def session(app_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(bind=app_engine, expire_on_commit=False, autoflush=False)
    async with factory() as s, s.begin():
        yield s


async def test_register_and_get_publisher(
    admin_engine: AsyncEngine, session: AsyncSession, clean_tables: None
) -> None:
    tenant_id = uuid4()
    await _seed_tenant(admin_engine, tenant_id)
    secret = os.urandom(32)

    publisher = await register_publisher(
        session,
        tenant_id=tenant_id,
        display_name="Test Org",
        hmac_secret=secret,
        jurisdictions=["GB"],
    )
    assert publisher.tenant_id == tenant_id
    assert publisher.reputation == 50
    assert publisher.revoked_at is None

    fetched = await get_publisher(session, tenant_id=tenant_id)
    assert fetched is not None
    assert fetched.display_name == "Test Org"
    assert fetched.hmac_secret == secret


async def test_update_reputation(
    admin_engine: AsyncEngine, session: AsyncSession, clean_tables: None
) -> None:
    tenant_id = uuid4()
    await _seed_tenant(admin_engine, tenant_id)
    await register_publisher(
        session, tenant_id=tenant_id, display_name="Org", hmac_secret=os.urandom(32)
    )

    await update_reputation(session, tenant_id=tenant_id, reputation=75)
    fetched = await get_publisher(session, tenant_id=tenant_id)
    assert fetched is not None
    assert fetched.reputation == 75


async def test_list_publishers_excludes_revoked(
    admin_engine: AsyncEngine, session: AsyncSession, clean_tables: None
) -> None:
    t1 = uuid4()
    t2 = uuid4()
    for tid in (t1, t2):
        await _seed_tenant(admin_engine, tid)
        await register_publisher(
            session, tenant_id=tid, display_name="Org", hmac_secret=os.urandom(32)
        )

    await revoke_publisher(session, tenant_id=t2)
    publishers = await list_publishers(session)
    ids = {p.tenant_id for p in publishers}
    assert t1 in ids
    assert t2 not in ids


async def test_reputation_event_round_trip(
    admin_engine: AsyncEngine, session: AsyncSession, clean_tables: None
) -> None:
    pub_id = uuid4()
    reporter_id = uuid4()
    for tid in (pub_id, reporter_id):
        await _seed_tenant(admin_engine, tid)
    await register_publisher(
        session, tenant_id=pub_id, display_name="Org", hmac_secret=os.urandom(32)
    )

    event = await insert_reputation_event(
        session,
        publisher_tenant_id=pub_id,
        reporter_tenant_id=reporter_id,
        delta=-5,
        reason="CONFIRM_FALSE",
    )
    assert event.delta == -5

    events = await list_events_for_publisher(session, publisher_tenant_id=pub_id)
    assert len(events) == 1
    assert events[0].reason == "CONFIRM_FALSE"
