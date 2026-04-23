# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime

import redis.asyncio as aioredis
from fastapi import APIRouter
from sqlalchemy import select

from services.response.app.stream_producer import enqueue_tier_change
from services.scoring.app.federation_dispatch import maybe_dispatch_federation
from services.scoring.app.repository import load_or_initialize, persist
from services.scoring.app.service import score_event
from shared.audit.events import record_event_scored, record_score_changed, record_tier_changed
from shared.config import get_settings
from shared.contracts.score import ScoreRequest, ScoreResponse
from shared.db.models import Tenant
from shared.db.session import tenant_session
from shared.explainability.evidence_templates import EVIDENCE_TEMPLATES
from shared.explainability.reasoning_generator import generate_reasoning
from shared.explainability.reasoning_repository import insert_reasoning
from shared.patterns.matches import DetectionMode, PatternMatch
from shared.response.tier_change import TierChangeEvent
from shared.schemas.enums import ResponseTier
from shared.schemas.reasoning import Reasoning

router = APIRouter(prefix="/internal", tags=["score"])


def _template_vars(
    evidence: str, confidence: float, pattern_name: str
) -> dict[str, str | int | float | bool]:
    phrase = evidence or pattern_name
    return {
        "matched_phrase": phrase,
        "excerpt": phrase,
        "confidence": round(confidence, 2),
        "distinct_minors": 0,
        "lookback_days": 0,
        "velocity_per_day": 0.0,
        "conversations": 0,
        "distinct_targets": 0,
        "similarity": 0.0,
        "flagged_neighbors": 0,
        "threshold": 0.0,
    }


def _signals_to_matches(payload: ScoreRequest) -> tuple[PatternMatch, ...]:
    return tuple(
        PatternMatch(
            pattern_name=signal.kind.value,
            signal_kind=signal.kind,
            confidence=signal.confidence,
            evidence_excerpts=(signal.evidence,) if signal.evidence else (),
            detection_mode=DetectionMode.RULE,
            prompt_version=None,
            template_variables=_template_vars(
                signal.evidence, signal.confidence, signal.kind.value
            ),
        )
        for signal in payload.signals
        if signal.kind.value in EVIDENCE_TEMPLATES
    )


@router.post("/score", response_model=ScoreResponse)
async def score(payload: ScoreRequest) -> ScoreResponse:
    now = datetime.now(UTC)
    reasoning: Reasoning | None = None
    federation_flags: dict[str, object] = {}
    async with tenant_session(payload.event.tenant_id) as session:
        profile = await load_or_initialize(
            session,
            tenant_id=payload.event.tenant_id,
            actor_id=payload.event.actor_id,
            now=now,
        )
        outcome = score_event(
            profile=profile,
            signals=payload.signals,
            event=payload.event,
            now=now,
        )
        await persist(
            session,
            event=payload.event,
            profile=outcome.profile,
            new_history=outcome.history_entries,
        )
        await record_event_scored(
            session,
            tenant_id=payload.event.tenant_id,
            actor_id=payload.event.actor_id,
            event_id=payload.event.id,
            signal_count=len(payload.signals),
            timestamp=now,
        )
        if outcome.delta != 0:
            await record_score_changed(
                session,
                tenant_id=payload.event.tenant_id,
                actor_id=payload.event.actor_id,
                previous_score=outcome.previous_score,
                new_score=outcome.new_score,
                delta=outcome.delta,
                cause="event",
                event_id=payload.event.id,
                timestamp=now,
            )
        if outcome.tier_changed:
            await record_tier_changed(
                session,
                tenant_id=payload.event.tenant_id,
                actor_id=payload.event.actor_id,
                previous_tier=int(outcome.previous_tier),
                new_tier=int(outcome.new_tier),
                triggering_score=outcome.new_score,
                timestamp=now,
            )
        tenant_row = (
            await session.execute(select(Tenant).where(Tenant.id == payload.event.tenant_id))
        ).scalar_one_or_none()
        if tenant_row is not None:
            federation_flags = dict(tenant_row.feature_flags or {})
        if outcome.tier_changed and outcome.new_tier > ResponseTier.TRUSTED:
            reasoning = generate_reasoning(
                actor_id=payload.event.actor_id,
                tenant_id=payload.event.tenant_id,
                previous_score=outcome.previous_score,
                new_score=outcome.new_score,
                new_tier=outcome.new_tier,
                matches=_signals_to_matches(payload),
                contact_graph=None,
                actor_memory=None,
                actor_age_days=None,
                action_kinds=(),
                generated_at=now,
            )
            await insert_reasoning(
                session,
                reasoning=reasoning,
                event_id=payload.event.id,
            )
    if outcome.tier_changed:
        settings = get_settings()
        redis = aioredis.from_url(settings.redis_dsn)
        try:
            await enqueue_tier_change(
                redis,
                stream_name=settings.response_tier_change_stream,
                event=TierChangeEvent(
                    tenant_id=payload.event.tenant_id,
                    actor_id=payload.event.actor_id,
                    event_id=payload.event.id,
                    previous_tier=outcome.previous_tier,
                    new_tier=outcome.new_tier,
                    new_score=outcome.new_score,
                    triggered_at=now,
                    reasoning=reasoning,
                ),
            )
        finally:
            await redis.aclose()  # type: ignore[attr-defined]
        signal_kinds = tuple(s.kind.value for s in payload.signals)
        maybe_dispatch_federation(
            tenant_id=payload.event.tenant_id,
            actor_id=payload.event.actor_id,
            new_tier=outcome.new_tier,
            tier_threshold=ResponseTier[settings.federation_publish_tier_threshold.upper()],
            federation_enabled=bool(federation_flags.get("federation_enabled")),
            federation_publish=bool(federation_flags.get("federation_publish")),
            signal_kinds=signal_kinds or ("risk_assessment",),
            flagged_at=now,
        )
    return ScoreResponse(
        current_score=outcome.new_score,
        previous_score=outcome.previous_score,
        delta=outcome.delta,
        tier=outcome.new_tier,
        reasoning=reasoning,
    )
