# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import asyncio
import logging
import time
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


async def _redeliver(
    redis: aioredis.Redis,  # type: ignore[type-arg]
    http: httpx.AsyncClient,
    fields: dict[bytes, bytes],
    *,
    now: datetime,
) -> None:
    settings = get_settings()
    event = TierChangeEvent.model_validate(orjson.loads(fields[b"data"]))
    attempt = int(fields.get(b"attempt", b"1"))
    async with tenant_session(event.tenant_id) as session:
        config = await load_or_create_config(session, tenant_id=event.tenant_id)
        endpoints = await list_endpoints_for_event(
            session, tenant_id=event.tenant_id, event_kind=WebhookEventKind.TIER_CHANGED
        )
    envelope = WebhookEnvelope(
        delivery_id=uuid4(),
        tenant_id=event.tenant_id,
        actor_id=event.actor_id,
        event_kind=WebhookEventKind.TIER_CHANGED,
        body={
            "previous_tier": int(event.previous_tier),
            "new_tier": int(event.new_tier),
            "new_score": event.new_score,
            "triggered_at": event.triggered_at.isoformat(),
        },
        produced_at=now,
    )
    failed = False
    for endpoint in endpoints:
        outcome = await deliver_webhook(
            http=http,
            url=str(endpoint.url),
            envelope=envelope,
            secret=config.webhook_secret,
            now=now,
            timeout_seconds=5.0,
        )
        if outcome != DeliveryOutcome.SUCCESS:
            failed = True
    if not failed:
        return
    if attempt >= settings.response_retry_max_attempts:
        await redis.xadd(
            settings.response_dead_letter_stream,
            {
                b"data": fields[b"data"],
                b"attempt": str(attempt).encode(),
                b"reason": b"retries_exhausted",
            },
        )
        return
    delay = next_retry_delay(
        attempt=attempt,
        base=settings.response_retry_base_delay_seconds,
        cap=settings.response_retry_max_delay_seconds,
    )
    await redis.xadd(
        settings.response_retry_stream,
        {
            b"data": fields[b"data"],
            b"attempt": str(attempt + 1).encode(),
            b"next_attempt_at": str(now.timestamp() + delay).encode(),
        },
    )


async def run_retry_worker(
    redis: aioredis.Redis,  # type: ignore[type-arg]
    *,
    stop_event: asyncio.Event,
    iteration_limit: int | None = None,
) -> None:
    settings = get_settings()
    stream = settings.response_retry_stream
    iterations = 0
    async with httpx.AsyncClient() as http:
        while not stop_event.is_set():
            if iteration_limit is not None and iterations >= iteration_limit:
                return
            iterations += 1
            entries = await redis.xrange(stream, count=50)
            if not entries:
                await asyncio.sleep(0.5)
                continue
            now = datetime.now(UTC)
            for entry_id, fields in entries:
                due = float(fields.get(b"next_attempt_at", b"0"))
                if due > time.time():
                    continue
                try:
                    await _redeliver(redis, http, fields, now=now)
                except Exception:
                    logger.exception("retry worker redeliver failed")
                await redis.xdel(stream, entry_id)
