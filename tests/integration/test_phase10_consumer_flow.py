# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import uuid4

import fakeredis.aioredis as fakeredis
import orjson
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.federation.app.consumer import run_federation_consumer
from services.federation.app.publisher import _envelope_to_dict, build_federation_signal
from services.federation.app.qdrant_federated import FederatedQdrantAdapter
from shared.federation.publisher_repository import register_publisher
from shared.federation.signal_repository import list_recent
from shared.fingerprint.repository import upsert_fingerprint
from shared.vector.qdrant_client import QdrantAdapter, get_qdrant_client

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_FP_COLLECTION = "actor_fingerprints"
_FED_COLLECTION = "test_fed_consumer_fingerprints"
_DIM = 16
_STREAM = "test:federation:signals:consumer"


async def _seed(engine: AsyncEngine, *tenant_ids) -> None:  # type: ignore[no-untyped-def]
    async with engine.begin() as conn:
        for tid in tenant_ids:
            await conn.execute(
                text(
                    "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                    "data_retention_days, feature_flags) VALUES (:t, 'consumer-test', 'free', '{}', 30, "
                    "'{}'::jsonb) ON CONFLICT DO NOTHING"
                ),
                {"t": str(tid)},
            )
            await conn.execute(
                text(
                    "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band, metadata) "
                    "VALUES (:a, :t, :h, 'unknown', '{}'::jsonb) ON CONFLICT DO NOTHING"
                ),
                {"a": str(tid), "t": str(tid), "h": "c" * 64},
            )


@pytest.fixture(autouse=True)
async def _clean_fed_collection() -> AsyncGenerator[None, None]:
    client = get_qdrant_client()
    existing = await client.get_collections()
    if any(c.name == _FED_COLLECTION for c in existing.collections):
        await client.delete_collection(_FED_COLLECTION)
    yield
    existing = await client.get_collections()
    if any(c.name == _FED_COLLECTION for c in existing.collections):
        await client.delete_collection(_FED_COLLECTION)


async def test_consumer_processes_valid_signal(
    admin_engine: AsyncEngine, app_engine: AsyncEngine, clean_tables: None
) -> None:
    pub_id = uuid4()
    receiver_id = uuid4()
    await _seed(admin_engine, pub_id, receiver_id)

    fp_adapter = QdrantAdapter(client=get_qdrant_client(), collection_name=_FP_COLLECTION, dim=_DIM)
    await fp_adapter.bootstrap()
    fp = tuple(float(i) / _DIM for i in range(_DIM))
    await upsert_fingerprint(fp_adapter, tenant_id=pub_id, actor_id=pub_id, vector=fp, flagged=True)

    hmac_secret = os.urandom(32)

    from sqlalchemy import text as _text

    factory = async_sessionmaker(bind=app_engine, expire_on_commit=False, autoflush=False)
    async with factory() as session, session.begin():
        await session.execute(
            _text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": str(pub_id)}
        )
        await register_publisher(
            session, tenant_id=pub_id, display_name="Pub", hmac_secret=hmac_secret
        )

    async with factory() as session, session.begin():
        await session.execute(
            _text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": str(pub_id)}
        )
        envelope = await build_federation_signal(
            session=session,
            tenant_id=pub_id,
            actor_id=pub_id,
            signal_kinds=("grooming",),
            flagged_at=datetime.now(UTC),
            adapter=fp_adapter,
        )

    redis = fakeredis.FakeRedis(decode_responses=False)
    payload = orjson.dumps(_envelope_to_dict(envelope))
    await redis.xadd(_STREAM, {"envelope": payload})

    fed_adapter = FederatedQdrantAdapter(
        client=get_qdrant_client(), collection_name=_FED_COLLECTION, dim=_DIM
    )
    await fed_adapter.bootstrap()

    stop_event = asyncio.Event()
    async with factory() as session, session.begin():
        await session.execute(
            _text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": str(receiver_id)}
        )
        await run_federation_consumer(
            redis,
            stream_name=_STREAM,
            qdrant_adapter=fed_adapter,
            session=session,
            receiver_tenant_id=receiver_id,
            stop_event=stop_event,
            iteration_limit=1,
        )

    async with factory() as session, session.begin():
        recent = await list_recent(session, limit=10)

    assert len(recent) == 1
    assert recent[0].publisher_tenant_id == pub_id

    neighbors = await fed_adapter.search(fingerprint=fp, top_k=5)
    assert len(neighbors) == 1
    assert neighbors[0].publisher_tenant_id == pub_id
