# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from shared.config import get_settings
from shared.contracts.graph import (
    ContactGraphLookupRequest,
    ContactGraphLookupResponse,
    FingerprintSimilarRequest,
    FingerprintSimilarResponse,
    FingerprintUpsertRequest,
)
from shared.db.session import tenant_session
from shared.fingerprint.repository import find_similar_actors, upsert_fingerprint
from shared.graph.edges import ContactEdgeRepository
from shared.vector.qdrant_client import QdrantAdapter, get_qdrant_client

router = APIRouter(prefix="/internal", tags=["graph"])


def _adapter() -> QdrantAdapter:
    settings = get_settings()
    return QdrantAdapter(
        client=get_qdrant_client(),
        collection_name=settings.qdrant_fingerprint_collection,
        dim=settings.fingerprint_vector_dim,
    )


@router.post("/contact-graph", response_model=ContactGraphLookupResponse)
async def contact_graph(payload: ContactGraphLookupRequest) -> ContactGraphLookupResponse:
    now = datetime.now(UTC)
    async with tenant_session(payload.tenant_id) as session:
        repo = ContactEdgeRepository(session)
        view = await repo.get_contact_graph(
            tenant_id=payload.tenant_id,
            actor_id=payload.actor_id,
            now=now,
            lookback_days=payload.lookback_days,
        )
    return ContactGraphLookupResponse(view=view)


@router.post("/fingerprint/upsert")
async def fingerprint_upsert(payload: FingerprintUpsertRequest) -> dict[str, str]:
    adapter = _adapter()
    await adapter.bootstrap()
    await upsert_fingerprint(
        adapter,
        tenant_id=payload.tenant_id,
        actor_id=payload.actor_id,
        vector=payload.vector,
        flagged=payload.flagged,
    )
    return {"status": "ok"}


@router.post("/fingerprint/similar", response_model=FingerprintSimilarResponse)
async def fingerprint_similar(payload: FingerprintSimilarRequest) -> FingerprintSimilarResponse:
    adapter = _adapter()
    await adapter.bootstrap()
    neighbors = await find_similar_actors(
        adapter,
        tenant_id=payload.tenant_id,
        vector=payload.vector,
        exclude_actor_id=payload.actor_id,
        top_k=payload.top_k,
    )
    return FingerprintSimilarResponse(neighbors=neighbors)
