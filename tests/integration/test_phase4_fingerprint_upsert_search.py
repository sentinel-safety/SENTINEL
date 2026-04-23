# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import uuid4

import pytest
from qdrant_client import AsyncQdrantClient

from shared.config import get_settings
from shared.fingerprint.repository import (
    FingerprintNeighbor,
    find_similar_actors,
    upsert_fingerprint,
)
from shared.vector.qdrant_client import QdrantAdapter

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _adapter() -> tuple[QdrantAdapter, AsyncQdrantClient]:
    settings = get_settings()
    client = AsyncQdrantClient(url=settings.qdrant_url, check_compatibility=False)
    adapter = QdrantAdapter(
        client=client, collection_name="test_phase4_fp", dim=settings.fingerprint_vector_dim
    )
    await adapter.bootstrap()
    return adapter, client


async def test_upsert_and_retrieve_round_trip() -> None:
    adapter, client = await _adapter()
    try:
        tenant_id = uuid4()
        actor_id = uuid4()
        vec = tuple(0.25 for _ in range(16))
        await upsert_fingerprint(
            adapter,
            tenant_id=tenant_id,
            actor_id=actor_id,
            vector=vec,
            flagged=False,
        )
        neighbors = await find_similar_actors(
            adapter, tenant_id=tenant_id, vector=vec, exclude_actor_id=uuid4(), top_k=5
        )
        assert any(n.actor_id == actor_id for n in neighbors)
        assert all(isinstance(n, FingerprintNeighbor) for n in neighbors)
    finally:
        await client.delete_collection("test_phase4_fp")
        await client.close()


async def test_tenant_filter_excludes_other_tenants() -> None:
    adapter, client = await _adapter()
    try:
        tenant_a = uuid4()
        tenant_b = uuid4()
        vec = tuple(0.25 for _ in range(16))
        await upsert_fingerprint(
            adapter, tenant_id=tenant_a, actor_id=uuid4(), vector=vec, flagged=True
        )
        await upsert_fingerprint(
            adapter, tenant_id=tenant_b, actor_id=uuid4(), vector=vec, flagged=True
        )
        neighbors = await find_similar_actors(
            adapter, tenant_id=tenant_a, vector=vec, exclude_actor_id=uuid4(), top_k=10
        )
        assert all(n.tenant_id == tenant_a for n in neighbors)
    finally:
        await client.delete_collection("test_phase4_fp")
        await client.close()
