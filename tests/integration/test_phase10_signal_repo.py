# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import os
import struct
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from shared.federation.publisher_repository import register_publisher
from shared.federation.signal_repository import insert_signal, list_recent
from shared.federation.tenant_secret_repository import get_or_create

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def _fp_bytes(vec: tuple[float, ...]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


async def _seed_tenant(engine: AsyncEngine, tenant_id) -> None:  # type: ignore[no-untyped-def]
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) VALUES (:t, 'sig-test', 'free', '{}', 30, "
                "'{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"t": str(tenant_id)},
        )


@pytest.fixture
async def session(app_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(bind=app_engine, expire_on_commit=False, autoflush=False)
    async with factory() as s, s.begin():
        yield s


async def test_signal_round_trip(
    admin_engine: AsyncEngine, session: AsyncSession, clean_tables: None
) -> None:
    pub_id = uuid4()
    await _seed_tenant(admin_engine, pub_id)
    await register_publisher(
        session, tenant_id=pub_id, display_name="Pub", hmac_secret=os.urandom(32)
    )

    fp = tuple(float(i) / 16 for i in range(16))
    fp_raw = _fp_bytes(fp)
    flagged_at = datetime.now(UTC)

    signal_id = await insert_signal(
        session,
        publisher_tenant_id=pub_id,
        fingerprint_bytes=fp_raw,
        signal_kinds=("grooming",),
        flagged_at=flagged_at,
        commit=b"\x00" * 32,
    )
    assert signal_id is not None

    recent = await list_recent(session, limit=10)
    assert len(recent) == 1
    assert recent[0].id == signal_id
    assert recent[0].publisher_tenant_id == pub_id
    assert all(abs(a - b) < 1e-5 for a, b in zip(recent[0].fingerprint, fp, strict=True))


async def _tenant_session(app_engine: AsyncEngine, tenant_id) -> AsyncSession:  # type: ignore[no-untyped-def]
    from sqlalchemy import text as _text

    factory = async_sessionmaker(bind=app_engine, expire_on_commit=False, autoflush=False)
    s = factory()
    await s.begin()
    await s.execute(
        _text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": str(tenant_id)}
    )
    return s


async def test_tenant_secret_get_or_create_idempotent(
    admin_engine: AsyncEngine, app_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    await _seed_tenant(admin_engine, tenant_id)

    s = await _tenant_session(app_engine, tenant_id)
    try:
        secret1 = await get_or_create(s, tenant_id=tenant_id)
        secret2 = await get_or_create(s, tenant_id=tenant_id)
        assert secret1.hmac_secret == secret2.hmac_secret
        assert secret1.actor_pepper == secret2.actor_pepper
        await s.commit()
    finally:
        await s.close()


async def test_tenant_secrets_are_isolated(
    admin_engine: AsyncEngine, app_engine: AsyncEngine, clean_tables: None
) -> None:
    t1 = uuid4()
    t2 = uuid4()
    for tid in (t1, t2):
        await _seed_tenant(admin_engine, tid)

    s1 = await _tenant_session(app_engine, t1)
    try:
        sec1 = await get_or_create(s1, tenant_id=t1)
        await s1.commit()
    finally:
        await s1.close()

    s2 = await _tenant_session(app_engine, t2)
    try:
        sec2 = await get_or_create(s2, tenant_id=t2)
        await s2.commit()
    finally:
        await s2.close()

    assert sec1.hmac_secret != sec2.hmac_secret
    assert sec1.actor_pepper != sec2.actor_pepper
