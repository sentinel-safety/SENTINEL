# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

import redis.asyncio as aioredis
from fastapi import APIRouter

from services.response.app.config_repository import load_or_create_config
from services.response.app.deadletter_repository import list_dead_letters
from services.response.app.stream_producer import enqueue_tier_change
from shared.config import get_settings
from shared.contracts.response import (
    DeadLetterListResponse,
    EvaluateResponseRequest,
    EvaluateResponseResponse,
)
from shared.db.session import tenant_session
from shared.response.action_defaults import recommend_actions

router = APIRouter(prefix="/internal/response", tags=["response"])


def _redis() -> aioredis.Redis:  # type: ignore[type-arg]
    return aioredis.from_url(get_settings().redis_dsn)


@router.post("/evaluate", response_model=EvaluateResponseResponse)
async def evaluate(payload: EvaluateResponseRequest) -> EvaluateResponseResponse:
    settings = get_settings()
    redis = _redis()
    try:
        await enqueue_tier_change(
            redis,
            stream_name=settings.response_tier_change_stream,
            event=payload.tier_change,
        )
    finally:
        await redis.aclose()  # type: ignore[attr-defined]
    async with tenant_session(payload.tier_change.tenant_id) as session:
        config = await load_or_create_config(session, tenant_id=payload.tier_change.tenant_id)
    actions = recommend_actions(payload.tier_change.new_tier, config)
    return EvaluateResponseResponse(
        enqueued=True,
        recommended_action_kinds=tuple(a.kind.value for a in actions),
    )


@router.get("/dead-letters/{tenant_id}", response_model=DeadLetterListResponse)
async def dead_letters(tenant_id: UUID) -> DeadLetterListResponse:
    settings = get_settings()
    redis = _redis()
    try:
        entries = await list_dead_letters(
            redis,
            stream_name=settings.response_dead_letter_stream,
            tenant_id=tenant_id,
            limit=100,
        )
    finally:
        await redis.aclose()  # type: ignore[attr-defined]
    return DeadLetterListResponse(entries=entries)
