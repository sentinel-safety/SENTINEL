# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import uuid4

import fakeredis.aioredis as fakeredis
import orjson
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.federation.app.publisher import build_federation_signal, publish_signal
from shared.federation.publisher_repository import register_publisher
from shared.federation.signals import FederationSignalEnvelope
from shared.fingerprint.repository import upsert_fingerprint
from shared.vector.qdrant_client import QdrantAdapter, get_qdrant_client

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_COLLECTION = "actor_fingerprints"
_DIM = 16
_STREAM = "federation:signals:test"


async def _seed_tenant_and_actor(engine: AsyncEngine, tenant_id, actor_id) -> None:  # type: ignore[no-untyped-def]
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) VALUES (:t, 'pub-flow', 'free', '{}', 30, "
                "'{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"t": str(tenant_id)},
        )
        await conn.execute(
            text(
                "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band, metadata) "
                "VALUES (:a, :t, :h, 'unknown', '{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"a": str(actor_id), "t": str(tenant_id), "h": "a" * 64},
        )


async def test_build_and_publish(
    admin_engine: AsyncEngine, app_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    await _seed_tenant_and_actor(admin_engine, tenant_id, actor_id)

    adapter = QdrantAdapter(
        client=get_qdrant_client(),
        collection_name=_COLLECTION,
        dim=_DIM,
    )
    await adapter.bootstrap()

    fp = tuple(float(i) / _DIM for i in range(_DIM))
    await upsert_fingerprint(
        adapter, tenant_id=tenant_id, actor_id=actor_id, vector=fp, flagged=True
    )

    from sqlalchemy import text as _text

    factory = async_sessionmaker(bind=app_engine, expire_on_commit=False, autoflush=False)
    async with factory() as session, session.begin():
        await register_publisher(
            session, tenant_id=tenant_id, display_name="Pub", hmac_secret=os.urandom(32)
        )

    async with factory() as session, session.begin():
        await session.execute(
            _text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": str(tenant_id)}
        )

        flagged_at = datetime.now(UTC)
        envelope = await build_federation_signal(
            session=session,
            tenant_id=tenant_id,
            actor_id=actor_id,
            signal_kinds=("grooming",),
            flagged_at=flagged_at,
            adapter=adapter,
        )

    assert isinstance(envelope, FederationSignalEnvelope)
    assert envelope.signal.publisher_tenant_id == tenant_id
    assert len(envelope.signal.fingerprint) == _DIM

    redis = fakeredis.FakeRedis(decode_responses=False)
    entry_id = await publish_signal(redis=redis, stream_name=_STREAM, envelope=envelope)
    assert entry_id is not None

    entries = await redis.xread({_STREAM: "0"})
    assert len(entries) == 1
    stream_entries = entries[0][1]
    assert len(stream_entries) == 1
    raw = stream_entries[0][1][b"envelope"]
    decoded = orjson.loads(raw)
    assert str(tenant_id) == decoded["signal"]["publisher_tenant_id"]
    assert len(decoded["signal"]["fingerprint"]) == _DIM
    assert decoded["signal"]["signal_kinds"] == ["grooming"]
    commit_bytes = bytes.fromhex(decoded["commit"])
    actor_hash_bytes = bytes.fromhex(decoded["signal"]["actor_hash"])
    assert len(commit_bytes) == 32
    assert len(actor_hash_bytes) == 32
