# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import redis.asyncio as aioredis
from fastapi import APIRouter, HTTPException, Query

from services.federation.app.publisher import build_federation_signal, publish_signal
from shared.config import get_settings
from shared.contracts.federation import (
    FeedResponse,
    FeedSignalItem,
    PublishRequest,
    PublishResponse,
    ReportFalseRequest,
    ReportFalseResponse,
)
from shared.db.session import get_session_factory, tenant_session
from shared.federation.publisher_repository import get_publisher, update_reputation
from shared.federation.reputation import ReputationDelta, adjust_reputation
from shared.federation.reputation_repository import insert_reputation_event
from shared.federation.signal_repository import list_recent
from shared.vector.qdrant_client import QdrantAdapter, get_qdrant_client

router = APIRouter(prefix="/internal/federation", tags=["federation"])


@router.post("/publish", response_model=PublishResponse)
async def publish(payload: PublishRequest) -> PublishResponse:
    settings = get_settings()
    adapter = QdrantAdapter(
        client=get_qdrant_client(),
        collection_name=settings.qdrant_fingerprint_collection,
        dim=settings.fingerprint_vector_dim,
    )
    redis: aioredis.Redis[bytes] = aioredis.from_url(settings.redis_dsn)
    try:
        async with tenant_session(payload.tenant_id) as session:
            envelope = await build_federation_signal(
                session=session,
                tenant_id=payload.tenant_id,
                actor_id=payload.actor_id,
                signal_kinds=payload.signal_kinds,
                flagged_at=payload.flagged_at,
                adapter=adapter,
            )
        entry_id = await publish_signal(
            redis=redis,
            stream_name=settings.federation_signals_stream,
            envelope=envelope,
        )
    finally:
        await redis.aclose()  # type: ignore[attr-defined]
    return PublishResponse(entry_id=entry_id)


@router.get("/feed", response_model=FeedResponse)
async def feed(limit: int = Query(default=100, ge=1, le=1000)) -> FeedResponse:
    factory = get_session_factory()
    async with factory() as session:
        signals = await list_recent(session, limit=limit)
    return FeedResponse(
        signals=tuple(
            FeedSignalItem(
                id=s.id,
                publisher_tenant_id=s.publisher_tenant_id,
                signal_kinds=s.signal_kinds,
                flagged_at=s.flagged_at,
            )
            for s in signals
        )
    )


@router.post("/report-false", response_model=ReportFalseResponse)
async def report_false(payload: ReportFalseRequest) -> ReportFalseResponse:
    async with tenant_session(payload.reporter_tenant_id) as session:
        publisher = await get_publisher(session, tenant_id=payload.reporter_tenant_id)
        if publisher is None:
            raise HTTPException(status_code=404, detail="publisher not found")
        new_rep = adjust_reputation(publisher.reputation, ReputationDelta.EXPLICIT_COMPLAINT.name)
        await update_reputation(session, tenant_id=publisher.tenant_id, reputation=new_rep)
        await insert_reputation_event(
            session,
            publisher_tenant_id=publisher.tenant_id,
            reporter_tenant_id=payload.reporter_tenant_id,
            delta=ReputationDelta.EXPLICIT_COMPLAINT,
            reason=payload.reason[:100],
        )
    return ReportFalseResponse(status="recorded")
