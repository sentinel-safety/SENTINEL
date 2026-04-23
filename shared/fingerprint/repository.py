# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID, uuid5

from shared.schemas.base import FrozenModel
from shared.vector.qdrant_client import QdrantAdapter

_NAMESPACE = UUID("1b3c3a3a-4d22-4b77-93a8-1d4e5f2c9e11")


class FingerprintNeighbor(FrozenModel):
    tenant_id: UUID
    actor_id: UUID
    score: float
    flagged: bool


def _point_id(tenant_id: UUID, actor_id: UUID) -> str:
    return str(uuid5(_NAMESPACE, f"{tenant_id}:{actor_id}"))


async def upsert_fingerprint(
    adapter: QdrantAdapter,
    *,
    tenant_id: UUID,
    actor_id: UUID,
    vector: tuple[float, ...],
    flagged: bool,
) -> None:
    await adapter.upsert(
        point_id=_point_id(tenant_id, actor_id),
        vector=vector,
        payload={
            "tenant_id": str(tenant_id),
            "actor_id": str(actor_id),
            "flagged": flagged,
        },
    )


async def find_similar_actors(
    adapter: QdrantAdapter,
    *,
    tenant_id: UUID,
    vector: tuple[float, ...],
    exclude_actor_id: UUID,
    top_k: int,
) -> tuple[FingerprintNeighbor, ...]:
    scored = await adapter.search(
        vector=vector,
        tenant_id=str(tenant_id),
        top_k=top_k,
        exclude_id=str(exclude_actor_id),
    )
    neighbors: list[FingerprintNeighbor] = []
    for point in scored:
        payload = point.payload or {}
        neighbors.append(
            FingerprintNeighbor(
                tenant_id=UUID(str(payload.get("tenant_id"))),
                actor_id=UUID(str(payload.get("actor_id"))),
                score=float(point.score),
                flagged=bool(payload.get("flagged", False)),
            )
        )
    return tuple(neighbors)
