# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import fakeredis.aioredis as fakeredis
import orjson
import pytest

from services.patterns.app.stream_producer import enqueue_for_llm
from shared.contracts.patterns import DetectRequest
from shared.contracts.preprocess import ExtractedFeatures
from shared.schemas.event import Event

pytestmark = pytest.mark.unit


def _request() -> DetectRequest:
    return DetectRequest(
        event=Event(
            id=uuid4(),
            tenant_id=uuid4(),
            actor_id=uuid4(),
            target_actor_ids=(uuid4(),),
            conversation_id=uuid4(),
            content_hash="b" * 64,
            timestamp=datetime.now(UTC),
            type="message",
        ),
        features=ExtractedFeatures(
            normalized_content="hello",
            language="en",
            token_count=1,
            contains_url=False,
            contains_contact_request=False,
            minor_recipient=False,
            late_night_local=False,
        ),
    )


@pytest.mark.asyncio
async def test_enqueue_writes_to_stream() -> None:
    redis = fakeredis.FakeRedis(decode_responses=False)
    req = _request()
    await enqueue_for_llm(redis, queue_name="patterns:llm-queue", request=req)
    entries = await redis.xrange("patterns:llm-queue")
    assert len(entries) == 1
    _, fields = entries[0]
    payload = orjson.loads(fields[b"data"])
    assert payload["event"]["id"] == str(req.event.id)


@pytest.mark.asyncio
async def test_enqueue_multiple_messages_ordered() -> None:
    redis = fakeredis.FakeRedis(decode_responses=False)
    for _ in range(3):
        await enqueue_for_llm(redis, queue_name="patterns:llm-queue", request=_request())
    entries = await redis.xrange("patterns:llm-queue")
    assert len(entries) == 3


@pytest.mark.asyncio
async def test_enqueue_preserves_detect_request_fields() -> None:
    redis = fakeredis.FakeRedis(decode_responses=False)
    req = _request()
    await enqueue_for_llm(redis, queue_name="test-queue", request=req)
    entries = await redis.xrange("test-queue")
    _, fields = entries[0]
    payload = orjson.loads(fields[b"data"])
    assert payload["features"]["normalized_content"] == "hello"
