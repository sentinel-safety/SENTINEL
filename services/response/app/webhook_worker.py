# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import orjson
import redis.asyncio as aioredis

from services.response.app.config_repository import load_or_create_config
from services.response.app.endpoint_repository import list_endpoints_for_event
from shared.config import get_settings
from shared.db.session import tenant_session
from shared.response.envelope import WebhookEnvelope, WebhookEventKind
from shared.response.retry import next_retry_delay
from shared.response.tier_change import TierChangeEvent
from shared.webhook.delivery import DeliveryOutcome, deliver_webhook

logger = logging.getLogger(__name__)

_GROUP = "response-workers"
_CONSUMER = "worker-0"
_ATTEMPT_FIELD = b"attempt"
_DATA_FIELD = b"data"
_NEXT_AT_FIELD = b"next_attempt_at"


async def _ensure_group(redis: aioredis.Redis, stream: str) -> None:  # type: ignore[type-arg]
    try:
        await redis.xgroup_create(stream, _GROUP, id="0", mkstream=True)
    except aioredis.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise


async def _dispatch(
    redis: aioredis.Redis,  # type: ignore[type-arg]
    http: httpx.AsyncClient,
    stream: str,
    entry_id: bytes,
    fields: dict[bytes, bytes],
    *,
    now: datetime,
) -> None:
    settings = get_settings()
    event = TierChangeEvent.model_validate(orjson.loads(fields[_DATA_FIELD]))
    attempt = int(fields.get(_ATTEMPT_FIELD, b"1"))
    async with tenant_session(event.tenant_id) as session:
        config = await load_or_create_config(session, tenant_id=event.tenant_id)
        endpoints = await list_endpoints_for_event(
            session, tenant_id=event.tenant_id, event_kind=WebhookEventKind.TIER_CHANGED
        )
    if not endpoints:
        await redis.xack(stream, _GROUP, entry_id)  # type: ignore[no-untyped-call]
        return
    envelope_body: dict[str, object] = {
        "previous_tier": int(event.previous_tier),
        "new_tier": int(event.new_tier),
        "new_score": event.new_score,
        "triggered_at": event.triggered_at.isoformat(),
    }
    if event.reasoning is not None:
        envelope_body["reasoning"] = event.reasoning.model_dump(mode="json")
    envelope = WebhookEnvelope(
        delivery_id=uuid4(),
        tenant_id=event.tenant_id,
        actor_id=event.actor_id,
        event_kind=WebhookEventKind.TIER_CHANGED,
        body=envelope_body,
        produced_at=now,
    )
    any_retryable = False
    any_permanent_fail = False
    for endpoint in endpoints:
        outcome = await deliver_webhook(
            http=http,
            url=str(endpoint.url),
            envelope=envelope,
            secret=config.webhook_secret,
            now=now,
            timeout_seconds=5.0,
        )
        if outcome == DeliveryOutcome.RETRYABLE:
            any_retryable = True
        elif outcome == DeliveryOutcome.NON_RETRYABLE:
            any_permanent_fail = True
    if any_retryable and attempt < settings.response_retry_max_attempts:
        delay = next_retry_delay(
            attempt=attempt,
            base=settings.response_retry_base_delay_seconds,
            cap=settings.response_retry_max_delay_seconds,
        )
        next_at = now.timestamp() + delay
        await redis.xadd(
            settings.response_retry_stream,
            {
                _DATA_FIELD: fields[_DATA_FIELD],
                _ATTEMPT_FIELD: str(attempt + 1).encode(),
                _NEXT_AT_FIELD: str(next_at).encode(),
            },
        )
    elif any_retryable or any_permanent_fail:
        await redis.xadd(
            settings.response_dead_letter_stream,
            {
                _DATA_FIELD: fields[_DATA_FIELD],
                _ATTEMPT_FIELD: str(attempt).encode(),
                b"reason": b"retries_exhausted" if any_retryable else b"non_retryable_http_status",
            },
        )
    await redis.xack(stream, _GROUP, entry_id)  # type: ignore[no-untyped-call]


async def run_webhook_worker(
    redis: aioredis.Redis,  # type: ignore[type-arg]
    *,
    stop_event: asyncio.Event,
    iteration_limit: int | None = None,
) -> None:
    settings = get_settings()
    stream = settings.response_tier_change_stream
    await _ensure_group(redis, stream)
    iterations = 0
    async with httpx.AsyncClient() as http:
        while not stop_event.is_set():
            if iteration_limit is not None and iterations >= iteration_limit:
                return
            iterations += 1
            resp = await redis.xreadgroup(
                _GROUP,
                _CONSUMER,
                streams={stream: ">"},
                count=10,
                block=settings.response_worker_block_ms,
            )
            if not resp:
                continue
            now = datetime.now(UTC)
            for _, entries in resp:
                for entry_id, fields in entries:
                    try:
                        await _dispatch(redis, http, stream, entry_id, fields, now=now)
                    except Exception:
                        logger.exception("webhook dispatch failed")
                        await redis.xack(stream, _GROUP, entry_id)  # type: ignore[no-untyped-call]
