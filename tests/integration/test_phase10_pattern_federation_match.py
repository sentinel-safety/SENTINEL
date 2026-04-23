# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from services.federation.app.qdrant_federated import FederatedQdrantAdapter
from services.patterns.app.main import create_app
from shared.config import get_settings
from shared.contracts.patterns import DetectRequest, DetectResponse
from shared.contracts.preprocess import ExtractedFeatures
from shared.fingerprint.features import compute_fingerprint
from shared.fingerprint.repository import upsert_fingerprint
from shared.schemas.enums import EventType
from shared.schemas.event import Event
from shared.vector.qdrant_client import QdrantAdapter, get_qdrant_client

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_SETTINGS = get_settings()
_FED_COLLECTION = _SETTINGS.federation_qdrant_collection
_FP_COLLECTION = _SETTINGS.qdrant_fingerprint_collection


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


async def _seed(engine: AsyncEngine, tenant_id, actor_id) -> None:  # type: ignore[no-untyped-def]
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) VALUES (:t, 'fed-match', 'free', '{}', 30, "
                "'{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"t": str(tenant_id)},
        )
        await conn.execute(
            text(
                "INSERT INTO actor (id, tenant_id, external_id_hash, claimed_age_band, metadata) "
                "VALUES (:a, :t, :h, 'unknown', '{}'::jsonb) ON CONFLICT DO NOTHING"
            ),
            {"a": str(actor_id), "t": str(tenant_id), "h": "f" * 64},
        )


async def test_detect_emits_federation_signal_match(
    admin_engine: AsyncEngine, clean_tables: None
) -> None:
    tenant_id = uuid4()
    actor_id = uuid4()
    publisher_id = uuid4()
    await _seed(admin_engine, tenant_id, actor_id)

    dim = _SETTINGS.fingerprint_vector_dim

    from services.patterns.app.repositories.feature_window import aggregate_window_from_rows

    now = datetime.now(UTC)
    actor_fingerprint = compute_fingerprint(
        aggregate_window_from_rows([], actor_id=actor_id, now=now)
    )

    fp_adapter = QdrantAdapter(client=get_qdrant_client(), collection_name=_FP_COLLECTION, dim=dim)
    await fp_adapter.bootstrap()
    await upsert_fingerprint(
        fp_adapter, tenant_id=tenant_id, actor_id=actor_id, vector=actor_fingerprint, flagged=True
    )

    non_zero_fp = tuple(float(i + 1) / dim for i in range(dim))

    fed_adapter = FederatedQdrantAdapter(
        client=get_qdrant_client(),
        collection_name=_FED_COLLECTION,
        dim=dim,
    )
    await fed_adapter.bootstrap()
    await fed_adapter.upsert_signal(
        signal_id=uuid4(),
        fingerprint=non_zero_fp,
        publisher_tenant_id=publisher_id,
        actor_hash="aa" * 32,
        flagged_at=datetime.now(UTC),
        reputation=80,
    )

    env_overrides = {
        "SENTINEL_FINGERPRINT_SIMILARITY_THRESHOLD": "0.01",
    }
    for k, v in env_overrides.items():
        os.environ[k] = v

    try:
        get_settings.cache_clear()

        request = DetectRequest(
            event=Event(
                id=uuid4(),
                tenant_id=tenant_id,
                actor_id=actor_id,
                target_actor_ids=(uuid4(),),
                conversation_id=uuid4(),
                content_hash="b" * 64,
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

        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/internal/detect",
                json=request.model_dump(mode="json"),
            )
        assert response.status_code == 200
        parsed = DetectResponse.model_validate(response.json())

        fed_matches = [m for m in parsed.matches if m.pattern_name == "federation_signal_match"]
        assert len(fed_matches) >= 1
        match = fed_matches[0]
        assert match.template_variables["publisher_tenant_id"] == str(publisher_id)
        assert match.template_variables["reputation"] == 80
    finally:
        for k in env_overrides:
            os.environ.pop(k, None)
        get_settings.cache_clear()
