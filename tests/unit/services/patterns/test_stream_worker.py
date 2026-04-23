# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from unittest.mock import patch
from uuid import uuid4

import fakeredis.aioredis as fakeredis
import pytest
import respx
from httpx import AsyncClient, Response

from services.patterns.app.stream_producer import enqueue_for_llm
from services.patterns.app.stream_worker import _CONSUMER_GROUP, run_worker
from shared.contracts.patterns import DetectRequest
from shared.contracts.preprocess import ExtractedFeatures
from shared.patterns import PatternMatch
from shared.patterns.matches import DetectionMode
from shared.schemas.enums import EventType
from shared.schemas.event import Event
from shared.scoring.signals import SignalKind

pytestmark = pytest.mark.unit

_SCORE_URL = "http://scoring:8004"


def _request() -> DetectRequest:
    return DetectRequest(
        event=Event(
            id=uuid4(),
            tenant_id=uuid4(),
            actor_id=uuid4(),
            target_actor_ids=(uuid4(),),
            conversation_id=uuid4(),
            content_hash="c" * 64,
            timestamp=datetime.now(UTC),
            type=EventType.MESSAGE,
        ),
        features=ExtractedFeatures(
            normalized_content="hello friend",
            language="en",
            token_count=2,
            contains_url=False,
            contains_contact_request=False,
            minor_recipient=True,
            late_night_local=False,
        ),
    )


def _fake_match() -> PatternMatch:
    return PatternMatch(
        pattern_name="friendship_forming",
        signal_kind=SignalKind.FRIENDSHIP_FORMING,
        confidence=0.8,
        evidence_excerpts=("hello friend",),
        detection_mode=DetectionMode.LLM,
        prompt_version="v1",
    )


@pytest.mark.asyncio
async def test_worker_processes_message_and_acks() -> None:
    redis = fakeredis.FakeRedis(decode_responses=False)
    req = _request()
    await enqueue_for_llm(redis, queue_name="patterns:llm-queue", request=req)

    stop = asyncio.Event()

    async def _fake_run_llm(request: DetectRequest) -> tuple[PatternMatch, ...]:
        stop.set()
        return (_fake_match(),)

    with (
        patch("services.patterns.app.stream_worker._run_llm_patterns", _fake_run_llm),
        respx.mock(base_url=_SCORE_URL) as mock_score,
    ):
        mock_score.post("/internal/score").mock(
            return_value=Response(
                200, json={"current_score": 10, "previous_score": 0, "delta": 10, "tier": "watch"}
            )
        )
        async with AsyncClient() as http:
            await run_worker(
                redis,
                queue_name="patterns:llm-queue",
                scoring_url=_SCORE_URL,
                http=http,
                stop_event=stop,
            )

    pending = await redis.xpending("patterns:llm-queue", _CONSUMER_GROUP)  # type: ignore[no-untyped-call]
    assert pending["pending"] == 0


@pytest.mark.asyncio
async def test_worker_skips_scoring_when_no_matches() -> None:
    redis = fakeredis.FakeRedis(decode_responses=False)
    req = _request()
    await enqueue_for_llm(redis, queue_name="patterns:llm-queue", request=req)

    stop = asyncio.Event()

    async def _no_matches(request: DetectRequest) -> tuple[PatternMatch, ...]:
        stop.set()
        return ()

    with (
        patch("services.patterns.app.stream_worker._run_llm_patterns", _no_matches),
        respx.mock(base_url=_SCORE_URL, assert_all_called=False) as mock_score,
    ):
        mock_score.post("/internal/score").mock(return_value=Response(200, json={}))
        async with AsyncClient() as http:
            await run_worker(
                redis,
                queue_name="patterns:llm-queue",
                scoring_url=_SCORE_URL,
                http=http,
                stop_event=stop,
            )

    assert not mock_score.calls


@pytest.mark.asyncio
async def test_worker_acks_even_on_llm_error() -> None:
    redis = fakeredis.FakeRedis(decode_responses=False)
    req = _request()
    await enqueue_for_llm(redis, queue_name="patterns:llm-queue", request=req)

    stop = asyncio.Event()
    call_count = 0

    async def _boom(request: DetectRequest) -> tuple[PatternMatch, ...]:
        nonlocal call_count
        call_count += 1
        stop.set()
        raise RuntimeError("llm failure")

    with patch("services.patterns.app.stream_worker._run_llm_patterns", _boom):
        async with AsyncClient() as http:
            await run_worker(
                redis,
                queue_name="patterns:llm-queue",
                scoring_url=_SCORE_URL,
                http=http,
                stop_event=stop,
            )

    assert call_count == 1
    pending = await redis.xpending("patterns:llm-queue", _CONSUMER_GROUP)  # type: ignore[no-untyped-call]
    assert pending["pending"] == 0


@pytest.mark.asyncio
async def test_worker_stops_immediately_when_stop_set_before_start() -> None:
    redis = fakeredis.FakeRedis(decode_responses=False)
    stop = asyncio.Event()
    stop.set()

    async with AsyncClient() as http:
        await run_worker(
            redis,
            queue_name="patterns:llm-queue",
            scoring_url=_SCORE_URL,
            http=http,
            stop_event=stop,
        )
