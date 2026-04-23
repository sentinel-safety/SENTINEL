# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import fakeredis.aioredis as fakeredis
import orjson
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from services.federation.app.consumer import run_federation_consumer
from services.federation.app.publisher import _envelope_to_dict, build_federation_signal
from services.federation.app.qdrant_federated import FederatedQdrantAdapter
from services.patterns.app.main import create_app as create_patterns_app
from shared.config import get_settings
from shared.contracts.patterns import DetectRequest, DetectResponse
from shared.contracts.preprocess import ExtractedFeatures
from shared.db.models import AuditLogEntry
from shared.db.session import tenant_session
from shared.federation.publisher_repository import register_publisher
from shared.federation.signal_repository import list_recent
from shared.fingerprint.repository import upsert_fingerprint
from shared.schemas.enums import EventType
from shared.schemas.event import Event
from shared.vector.qdrant_client import QdrantAdapter, get_qdrant_client

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_DIM = 16
_FP_COLLECTION = "actor_fingerprints"
_FED_COLLECTION = "acceptance_test_federated_fingerprints"
_STREAM = "acceptance:federation:signals"
_SETTINGS = get_settings()


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


async def _seed_tenant(
    engine: AsyncEngine,
    tenant_id: UUID,
    name: str,
    actor_id: UUID,
    actor_hash_prefix: str,
) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                f"VALUES ('{tenant_id}', '{name}', 'free', '{{}}', 30, '{{}}'::jsonb)"
                " ON CONFLICT DO NOTHING"
            )
        )
        await conn.execute(
            text(
                "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band, metadata) "
                f"VALUES ('{actor_id}', '{tenant_id}', '{actor_hash_prefix * 64}', 'unknown', '{{}}'::jsonb)"
                " ON CONFLICT DO NOTHING"
            )
        )


async def test_three_tenant_publish_consume_match_audit(
    admin_engine: AsyncEngine, app_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_a = uuid4()
    tenant_b = uuid4()
    tenant_c = uuid4()
    actor_x = uuid4()
    actor_y = uuid4()
    actor_z = uuid4()

    await _seed_tenant(admin_engine, tenant_a, "TenantA", actor_x, "a")
    await _seed_tenant(admin_engine, tenant_b, "TenantB", actor_y, "b")
    await _seed_tenant(admin_engine, tenant_c, "TenantC", actor_z, "c")

    known_fp = tuple(float(i + 1) / _DIM for i in range(_DIM))
    fp_adapter = QdrantAdapter(client=get_qdrant_client(), collection_name=_FP_COLLECTION, dim=_DIM)
    await fp_adapter.bootstrap()
    await upsert_fingerprint(
        fp_adapter, tenant_id=tenant_a, actor_id=actor_x, vector=known_fp, flagged=True
    )

    hmac_secret = os.urandom(32)
    factory = async_sessionmaker(bind=app_engine, expire_on_commit=False, autoflush=False)

    async with tenant_session(tenant_a) as session:
        await register_publisher(
            session, tenant_id=tenant_a, display_name="A", hmac_secret=hmac_secret
        )

    flagged_at = datetime.now(UTC)
    async with tenant_session(tenant_a) as session:
        envelope = await build_federation_signal(
            session=session,
            tenant_id=tenant_a,
            actor_id=actor_x,
            signal_kinds=("risk_assessment",),
            flagged_at=flagged_at,
            adapter=fp_adapter,
        )

    redis = fakeredis.FakeRedis(decode_responses=False)
    payload_bytes = orjson.dumps(_envelope_to_dict(envelope))
    await redis.xadd(_STREAM, {"envelope": payload_bytes})

    assert str(actor_x) not in payload_bytes.decode("utf-8", errors="ignore")

    fed_adapter = FederatedQdrantAdapter(
        client=get_qdrant_client(), collection_name=_FED_COLLECTION, dim=_DIM
    )
    await fed_adapter.bootstrap()

    stop_event = asyncio.Event()
    async with tenant_session(tenant_b) as session:
        await run_federation_consumer(
            redis,
            stream_name=_STREAM,
            qdrant_adapter=fed_adapter,
            session=session,
            receiver_tenant_id=tenant_b,
            stop_event=stop_event,
            iteration_limit=1,
        )

    async with factory() as session:
        recent = await list_recent(session, limit=10)
    assert len(recent) == 1
    assert recent[0].publisher_tenant_id == tenant_a

    neighbors = await fed_adapter.search(fingerprint=known_fp, top_k=5)
    assert len(neighbors) == 1
    assert neighbors[0].publisher_tenant_id == tenant_a

    await upsert_fingerprint(
        fp_adapter, tenant_id=tenant_b, actor_id=actor_y, vector=known_fp, flagged=False
    )
    await upsert_fingerprint(
        fp_adapter, tenant_id=tenant_c, actor_id=actor_z, vector=known_fp, flagged=False
    )

    import os as _os

    _os.environ["SENTINEL_FINGERPRINT_SIMILARITY_THRESHOLD"] = "0.01"
    _os.environ["SENTINEL_FEDERATION_QDRANT_COLLECTION"] = _FED_COLLECTION
    get_settings.cache_clear()

    try:
        patterns_app = create_patterns_app()
        transport = ASGITransport(app=patterns_app)

        for receiver_tenant, receiver_actor in [(tenant_b, actor_y), (tenant_c, actor_z)]:
            req = DetectRequest(
                event=Event(
                    id=uuid4(),
                    tenant_id=receiver_tenant,
                    actor_id=receiver_actor,
                    target_actor_ids=(uuid4(),),
                    conversation_id=uuid4(),
                    content_hash="d" * 64,
                    timestamp=datetime.now(UTC),
                    type=EventType.MESSAGE,
                ),
                features=ExtractedFeatures(
                    normalized_content="hello",
                    language="en",
                    token_count=1,
                    contains_url=False,
                    contains_contact_request=False,
                    minor_recipient=False,
                    late_night_local=False,
                ),
            )
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.post("/internal/detect", json=req.model_dump(mode="json"))
            assert resp.status_code == 200
            parsed = DetectResponse.model_validate(resp.json())
            fed_matches = [m for m in parsed.matches if m.pattern_name == "federation_signal_match"]
            assert len(fed_matches) >= 1, f"no fed match for tenant {receiver_tenant}"
            assert fed_matches[0].template_variables["publisher_tenant_id"] == str(tenant_a)
    finally:
        _os.environ.pop("SENTINEL_FINGERPRINT_SIMILARITY_THRESHOLD", None)
        _os.environ.pop("SENTINEL_FEDERATION_QDRANT_COLLECTION", None)
        get_settings.cache_clear()

    all_audit_rows: list[AuditLogEntry] = []
    for tid in (tenant_a, tenant_b):
        async with tenant_session(tid) as session:
            rows = (
                (
                    await session.execute(
                        select(AuditLogEntry).where(
                            AuditLogEntry.event_type.in_(
                                ["federation.published", "federation.received"]
                            )
                        )
                    )
                )
                .scalars()
                .all()
            )
            all_audit_rows.extend(rows)
    audit_rows = all_audit_rows
    assert len(audit_rows) >= 1

    recv_audit = [r for r in audit_rows if r.event_type == "federation.received"]
    assert len(recv_audit) >= 1

    raw_actor_x_str = str(actor_x)
    for audit_row in audit_rows:
        details_json = orjson.dumps(audit_row.details)
        assert (
            raw_actor_x_str.encode() not in details_json
        ), f"raw actor_x UUID found in audit details: {audit_row.details}"

    recv_publisher_ids = {r.details.get("publisher_tenant_id") for r in recv_audit if r.details}
    assert str(tenant_a) in recv_publisher_ids

    raw_actor_bytes = str(actor_x).encode()
    all_stream_entries = await redis.xrange(_STREAM)
    for _entry_id, fields in all_stream_entries:
        envelope_bytes = fields.get(b"envelope", b"")
        assert raw_actor_bytes not in envelope_bytes, "raw actor_id found in Redis stream payload"
