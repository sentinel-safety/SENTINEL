# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import asyncio
import logging

import httpx
import orjson
import redis.asyncio as aioredis

from services.patterns.app.registry import build_llm_patterns
from services.patterns.app.repositories.event_lookback import EventLookback
from shared.contracts.patterns import DetectRequest
from shared.contracts.score import ScoreRequest
from shared.db.session import tenant_session
from shared.llm.factory import build_llm_provider
from shared.patterns import LLMPatternContext, PatternMatch
from shared.scoring.signals import ScoreSignal

logger = logging.getLogger(__name__)

_BLOCK_MS = 2000
_CONSUMER_GROUP = "patterns-llm-workers"
_CONSUMER_NAME = "worker-0"


async def _claim_group(redis: aioredis.Redis[bytes], queue_name: str) -> None:
    try:
        await redis.xgroup_create(queue_name, _CONSUMER_GROUP, id="0", mkstream=True)
    except aioredis.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


async def _recent_messages(request: DetectRequest) -> tuple[str, ...]:
    async with tenant_session(request.event.tenant_id) as session:
        lookback = EventLookback(session=session)
        return await lookback.fetch_recent_messages_for_actor(
            tenant_id=request.event.tenant_id,
            actor_id=request.event.actor_id,
            limit=10,
        )


async def _run_llm_patterns(request: DetectRequest) -> tuple[PatternMatch, ...]:
    from shared.config import get_settings

    provider = build_llm_provider(get_settings())
    patterns = build_llm_patterns(provider)
    recent = await _recent_messages(request)
    ctx = LLMPatternContext(
        event=request.event,
        features=request.features,
        recent_messages=recent,
    )
    all_matches: list[PatternMatch] = []
    for pattern in patterns:
        matches = await pattern.detect_llm(ctx)
        all_matches.extend(matches)
    return tuple(all_matches)


async def _post_signals(
    http: httpx.AsyncClient,
    scoring_url: str,
    request: DetectRequest,
    matches: tuple[PatternMatch, ...],
) -> None:
    if not matches:
        return
    signals = tuple(
        ScoreSignal(
            kind=m.signal_kind, confidence=m.confidence, evidence="; ".join(m.evidence_excerpts)
        )
        for m in matches
    )
    body = ScoreRequest(event=request.event, signals=signals).model_dump(mode="json")
    response = await http.post(f"{scoring_url}/internal/score", json=body)
    response.raise_for_status()


async def run_worker(
    redis: aioredis.Redis[bytes],
    *,
    queue_name: str,
    scoring_url: str,
    http: httpx.AsyncClient,
    stop_event: asyncio.Event | None = None,
) -> None:
    await _claim_group(redis, queue_name)

    while stop_event is None or not stop_event.is_set():
        entries = await redis.xreadgroup(
            _CONSUMER_GROUP,
            _CONSUMER_NAME,
            {queue_name: ">"},
            count=10,
            block=_BLOCK_MS,
        )
        if not entries:
            continue
        _, messages = entries[0]
        for message_id, fields in messages:
            try:
                payload = orjson.loads(fields[b"data"])
                request = DetectRequest.model_validate(payload)
                matches = await _run_llm_patterns(request)
                await _post_signals(http, scoring_url, request, matches)
            except Exception:
                logger.exception("llm worker failed processing message %s", message_id)
            finally:
                await redis.xack(queue_name, _CONSUMER_GROUP, message_id)  # type: ignore[no-untyped-call]
