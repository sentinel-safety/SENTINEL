# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qm
from qdrant_client.http.exceptions import UnexpectedResponse

from shared.config import get_settings


@lru_cache(maxsize=1)
def get_qdrant_client() -> AsyncQdrantClient:
    return AsyncQdrantClient(url=get_settings().qdrant_url, check_compatibility=False)


@dataclass
class QdrantAdapter:
    client: AsyncQdrantClient
    collection_name: str
    dim: int

    async def bootstrap(self) -> None:
        existing = await self.client.get_collections()
        if any(c.name == self.collection_name for c in existing.collections):
            return
        try:
            await self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qm.VectorParams(size=self.dim, distance=qm.Distance.COSINE),
            )
        except UnexpectedResponse as exc:
            if exc.status_code != 409:
                raise

    async def upsert(
        self,
        *,
        point_id: str,
        vector: tuple[float, ...],
        payload: dict[str, Any],
    ) -> None:
        await self.client.upsert(
            collection_name=self.collection_name,
            points=[qm.PointStruct(id=point_id, vector=list(vector), payload=payload)],
        )

    async def search(
        self,
        *,
        vector: tuple[float, ...],
        tenant_id: str,
        top_k: int,
        exclude_id: str | None = None,
    ) -> list[qm.ScoredPoint]:
        must = [qm.FieldCondition(key="tenant_id", match=qm.MatchValue(value=tenant_id))]
        must_not = []
        if exclude_id is not None:
            must_not.append(
                qm.FieldCondition(key="actor_id", match=qm.MatchValue(value=exclude_id))
            )
        filt = qm.Filter(must=must, must_not=must_not or None)
        result = await self.client.query_points(
            collection_name=self.collection_name,
            query=list(vector),
            query_filter=filt,
            limit=top_k,
            with_payload=True,
        )
        return result.points
