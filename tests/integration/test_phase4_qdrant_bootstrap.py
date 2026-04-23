# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest
from qdrant_client import AsyncQdrantClient

from shared.config import get_settings
from shared.vector.qdrant_client import QdrantAdapter

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def test_bootstrap_creates_collection_idempotently() -> None:
    settings = get_settings()
    client = AsyncQdrantClient(url=settings.qdrant_url, check_compatibility=False)
    try:
        adapter = QdrantAdapter(
            client=client,
            collection_name="test_phase4_bootstrap",
            dim=settings.fingerprint_vector_dim,
        )
        await adapter.bootstrap()
        await adapter.bootstrap()
        collections = await client.get_collections()
        names = {c.name for c in collections.collections}
        assert "test_phase4_bootstrap" in names
        await client.delete_collection("test_phase4_bootstrap")
    finally:
        await client.close()
