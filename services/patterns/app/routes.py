# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.federation.app.qdrant_federated import FederatedNeighbor, FederatedQdrantAdapter
from services.patterns.app.registry import SYNC_PATTERNS
from services.patterns.app.repositories.event_lookback import EventLookback
from services.patterns.app.repositories.feature_window import (
    aggregate_window_from_rows,
    fetch_window_rows,
)
from services.patterns.app.repositories.pattern_match_writes import persist_pattern_matches
from services.patterns.app.service import run_sync_patterns
from services.patterns.app.stream_producer import enqueue_for_llm
from shared.audit.events import record_pattern_matched
from shared.config import get_settings
from shared.contracts.patterns import DetectRequest, DetectResponse
from shared.db.event_writes import ensure_event_rows
from shared.db.models import SuspicionProfile
from shared.db.session import tenant_session
from shared.fingerprint.features import compute_fingerprint
from shared.fingerprint.repository import find_similar_actors, upsert_fingerprint
from shared.graph.edges import ContactEdgeRepository
from shared.memory import get_actor_memory
from shared.patterns.matches import DetectionMode, PatternMatch
from shared.scoring.signals import SignalKind
from shared.vector.qdrant_client import QdrantAdapter, get_qdrant_client

router = APIRouter()


def _federation_matches(
    neighbors: tuple[FederatedNeighbor, ...],
    *,
    threshold: float,
    low_reputation_threshold: int,
) -> list[PatternMatch]:
    matches = []
    for neighbor in neighbors:
        if neighbor.score < threshold:
            continue
        effective_confidence = neighbor.score * (neighbor.reputation / 100)
        low_rep = neighbor.reputation < low_reputation_threshold
        excerpt = (
            f"federated fingerprint match from publisher {neighbor.publisher_tenant_id} "
            f"with reputation {neighbor.reputation}"
            + (" (low-reputation publisher, confidence weighted down)" if low_rep else "")
        )
        matches.append(
            PatternMatch(
                pattern_name="federation_signal_match",
                signal_kind=SignalKind.FEDERATION_SIGNAL_MATCH,
                confidence=round(effective_confidence, 4),
                evidence_excerpts=(excerpt,),
                detection_mode=DetectionMode.RULE,
                template_variables={
                    "publisher_tenant_id": str(neighbor.publisher_tenant_id),
                    "similarity": round(neighbor.score, 3),
                    "reputation": neighbor.reputation,
                },
            )
        )
    return matches


def _age_band_for_event(request: DetectRequest) -> str:
    if request.features.minor_recipient:
        bands = request.event.content_features.get("recipient_age_bands")
        if isinstance(bands, list) and bands:
            return str(bands[0])
        return "under_13"
    return "18_plus"


async def _actor_is_flagged(session: AsyncSession, *, tenant_id: UUID, actor_id: UUID) -> bool:
    stmt = select(SuspicionProfile.tier).where(
        SuspicionProfile.tenant_id == tenant_id,
        SuspicionProfile.actor_id == actor_id,
    )
    row = (await session.execute(stmt)).first()
    if row is None:
        return False
    return int(row.tier) >= 4


@router.post("/internal/detect", response_model=DetectResponse)
async def detect(request: DetectRequest, http_request: Request) -> DetectResponse:
    settings = get_settings()
    now = datetime.now(UTC)
    tenant_id = request.event.tenant_id
    actor_id = request.event.actor_id
    adapter = QdrantAdapter(
        client=get_qdrant_client(),
        collection_name=settings.qdrant_fingerprint_collection,
        dim=settings.fingerprint_vector_dim,
    )
    await adapter.bootstrap()

    async with tenant_session(tenant_id) as session:
        await ensure_event_rows(session, request.event)

        edge_repo = ContactEdgeRepository(session)
        age_band = _age_band_for_event(request)
        for target_id in request.event.target_actor_ids:
            await edge_repo.record_interaction(
                tenant_id=tenant_id,
                source_actor_id=actor_id,
                target_actor_id=target_id,
                occurred_at=request.event.timestamp,
                target_age_band=age_band,
            )

        lookback = EventLookback(session=session)
        count = await lookback.count_distinct_minor_targets(
            tenant_id=tenant_id,
            actor_id=actor_id,
            window=timedelta(hours=24),
        )
        memory = await get_actor_memory(
            session,
            tenant_id=tenant_id,
            actor_id=actor_id,
            now=now,
            lookback=timedelta(days=settings.memory_lookback_days),
        )
        contact_graph = await edge_repo.get_contact_graph(
            tenant_id=tenant_id,
            actor_id=actor_id,
            now=now,
            lookback_days=settings.graph_lookback_days,
        )

        since = now - timedelta(days=settings.graph_lookback_days)
        rows = await fetch_window_rows(session, tenant_id=tenant_id, actor_id=actor_id, since=since)
        feature_window = aggregate_window_from_rows(rows, actor_id=actor_id, now=now)
        fingerprint = compute_fingerprint(feature_window)
        flagged = await _actor_is_flagged(session, tenant_id=tenant_id, actor_id=actor_id)
        await upsert_fingerprint(
            adapter,
            tenant_id=tenant_id,
            actor_id=actor_id,
            vector=fingerprint,
            flagged=flagged,
        )
        neighbors = await find_similar_actors(
            adapter,
            tenant_id=tenant_id,
            vector=fingerprint,
            exclude_actor_id=actor_id,
            top_k=settings.fingerprint_search_top_k,
        )

        fed_adapter = FederatedQdrantAdapter(
            client=get_qdrant_client(),
            collection_name=settings.federation_qdrant_collection,
            dim=settings.fingerprint_vector_dim,
        )
        await fed_adapter.bootstrap()
        fed_neighbors = await fed_adapter.search(
            fingerprint=fingerprint,
            top_k=settings.fingerprint_search_top_k,
            excluded_publisher_tenant_id=tenant_id,
        )
        fed_matches = _federation_matches(
            fed_neighbors,
            threshold=settings.fingerprint_similarity_threshold,
            low_reputation_threshold=settings.federation_low_reputation_threshold,
        )

        result = await run_sync_patterns(
            request,
            SYNC_PATTERNS,
            recent_distinct_minor_target_count=count,
            actor_memory=memory,
            contact_graph=contact_graph,
            fingerprint_neighbors=neighbors,
        )
        all_matches = result.matches + tuple(fed_matches)
        matched_ids = await persist_pattern_matches(
            session,
            tenant_id=tenant_id,
            actor_id=actor_id,
            event_id=request.event.id,
            matches=all_matches,
            matched_at=now,
        )
        for match, match_id in zip(all_matches, matched_ids, strict=True):
            await record_pattern_matched(
                session,
                tenant_id=tenant_id,
                actor_id=actor_id,
                pattern_name=match.pattern_name,
                confidence=match.confidence,
                event_id=request.event.id,
                pattern_match_id=match_id,
                timestamp=now,
            )

    redis = getattr(http_request.app.state, "redis", None)
    if redis is not None:
        await enqueue_for_llm(
            redis,
            queue_name=settings.patterns_llm_queue_name,
            request=request,
        )
    return DetectResponse(matches=all_matches, matched_ids=matched_ids)
