# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import uuid4

import pytest

from services.federation.app.qdrant_federated import FederatedNeighbor, FederatedQdrantAdapter
from shared.vector.qdrant_client import get_qdrant_client

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_DIM = 16
_COLLECTION = "test_federated_fingerprints"


@pytest.fixture(autouse=True)
async def _clean_collection() -> AsyncGenerator[None, None]:
    client = get_qdrant_client()
    existing = await client.get_collections()
    if any(c.name == _COLLECTION for c in existing.collections):
        await client.delete_collection(_COLLECTION)
    yield
    existing = await client.get_collections()
    if any(c.name == _COLLECTION for c in existing.collections):
        await client.delete_collection(_COLLECTION)


async def test_bootstrap_creates_collection() -> None:
    adapter = FederatedQdrantAdapter(
        client=get_qdrant_client(), collection_name=_COLLECTION, dim=_DIM
    )
    await adapter.bootstrap()
    existing = await get_qdrant_client().get_collections()
    names = {c.name for c in existing.collections}
    assert _COLLECTION in names


async def test_bootstrap_is_idempotent() -> None:
    adapter = FederatedQdrantAdapter(
        client=get_qdrant_client(), collection_name=_COLLECTION, dim=_DIM
    )
    await adapter.bootstrap()
    await adapter.bootstrap()


async def test_upsert_and_search() -> None:
    adapter = FederatedQdrantAdapter(
        client=get_qdrant_client(), collection_name=_COLLECTION, dim=_DIM
    )
    await adapter.bootstrap()

    signal_id = uuid4()
    publisher_id = uuid4()
    fp = tuple(0.1 * i for i in range(_DIM))
    flagged_at = datetime.now(UTC)

    await adapter.upsert_signal(
        signal_id=signal_id,
        fingerprint=fp,
        publisher_tenant_id=publisher_id,
        actor_hash="deadbeef" * 8,
        flagged_at=flagged_at,
        reputation=70,
    )

    results = await adapter.search(fingerprint=fp, top_k=5)
    assert len(results) == 1
    neighbor = results[0]
    assert isinstance(neighbor, FederatedNeighbor)
    assert neighbor.signal_id == signal_id
    assert neighbor.publisher_tenant_id == publisher_id
    assert neighbor.reputation == 70
    assert neighbor.score > 0.99


async def test_search_excludes_publisher() -> None:
    adapter = FederatedQdrantAdapter(
        client=get_qdrant_client(), collection_name=_COLLECTION, dim=_DIM
    )
    await adapter.bootstrap()

    publisher_id = uuid4()
    fp = tuple(0.1 * i for i in range(_DIM))

    await adapter.upsert_signal(
        signal_id=uuid4(),
        fingerprint=fp,
        publisher_tenant_id=publisher_id,
        actor_hash="ab" * 32,
        flagged_at=datetime.now(UTC),
        reputation=50,
    )

    results = await adapter.search(
        fingerprint=fp, top_k=5, excluded_publisher_tenant_id=publisher_id
    )
    assert len(results) == 0
