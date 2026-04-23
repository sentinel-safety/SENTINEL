# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qm
from qdrant_client.http.exceptions import UnexpectedResponse

from shared.schemas.base import FrozenModel


class FederatedNeighbor(FrozenModel):
    signal_id: UUID
    publisher_tenant_id: UUID
    actor_hash: str
    score: float
    flagged_at: datetime
    reputation: int


@dataclass
class FederatedQdrantAdapter:
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

    async def upsert_signal(
        self,
        *,
        signal_id: UUID,
        fingerprint: tuple[float, ...],
        publisher_tenant_id: UUID,
        actor_hash: str,
        flagged_at: datetime,
        reputation: int,
    ) -> None:
        await self.client.upsert(
            collection_name=self.collection_name,
            points=[
                qm.PointStruct(
                    id=str(signal_id),
                    vector=list(fingerprint),
                    payload={
                        "signal_id": str(signal_id),
                        "publisher_tenant_id": str(publisher_tenant_id),
                        "actor_hash": actor_hash,
                        "flagged_at": flagged_at.isoformat(),
                        "reputation": reputation,
                    },
                )
            ],
        )

    async def search(
        self,
        *,
        fingerprint: tuple[float, ...],
        top_k: int,
        excluded_publisher_tenant_id: UUID | None = None,
    ) -> tuple[FederatedNeighbor, ...]:
        must_not = []
        if excluded_publisher_tenant_id is not None:
            must_not.append(
                qm.FieldCondition(
                    key="publisher_tenant_id",
                    match=qm.MatchValue(value=str(excluded_publisher_tenant_id)),
                )
            )
        filt = qm.Filter(must_not=must_not or None) if must_not else None
        result = await self.client.query_points(
            collection_name=self.collection_name,
            query=list(fingerprint),
            query_filter=filt,
            limit=top_k,
            with_payload=True,
        )
        neighbors = []
        for point in result.points:
            payload = point.payload or {}
            neighbors.append(
                FederatedNeighbor(
                    signal_id=UUID(str(payload["signal_id"])),
                    publisher_tenant_id=UUID(str(payload["publisher_tenant_id"])),
                    actor_hash=str(payload["actor_hash"]),
                    score=float(point.score),
                    flagged_at=datetime.fromisoformat(str(payload["flagged_at"])),
                    reputation=int(payload["reputation"]),
                )
            )
        return tuple(neighbors)
