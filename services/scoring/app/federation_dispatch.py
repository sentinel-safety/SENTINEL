# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from uuid import UUID

import redis.asyncio as aioredis

from services.federation.app.publisher import build_federation_signal, publish_signal
from shared.config import get_settings
from shared.db.session import tenant_session
from shared.schemas.enums import ResponseTier
from shared.vector.qdrant_client import QdrantAdapter, get_qdrant_client

_log = logging.getLogger(__name__)


async def _publish(
    *,
    tenant_id: UUID,
    actor_id: UUID,
    signal_kinds: tuple[str, ...],
    flagged_at: datetime,
) -> None:
    settings = get_settings()
    adapter = QdrantAdapter(
        client=get_qdrant_client(),
        collection_name=settings.qdrant_fingerprint_collection,
        dim=settings.fingerprint_vector_dim,
    )
    redis: aioredis.Redis[bytes] = aioredis.from_url(settings.redis_dsn)
    try:
        async with tenant_session(tenant_id) as session:
            envelope = await build_federation_signal(
                session=session,
                tenant_id=tenant_id,
                actor_id=actor_id,
                signal_kinds=signal_kinds,
                flagged_at=flagged_at,
                adapter=adapter,
            )
        await publish_signal(
            redis=redis,
            stream_name=settings.federation_signals_stream,
            envelope=envelope,
        )
    except Exception as exc:
        _log.warning("federation dispatch failed: %s", exc)
    finally:
        await redis.aclose()  # type: ignore[attr-defined]


def maybe_dispatch_federation(
    *,
    tenant_id: UUID,
    actor_id: UUID,
    new_tier: ResponseTier,
    tier_threshold: int,
    federation_enabled: bool,
    federation_publish: bool,
    signal_kinds: tuple[str, ...],
    flagged_at: datetime,
) -> None:
    if int(new_tier) < tier_threshold:
        return
    if not federation_enabled or not federation_publish:
        return
    task = asyncio.ensure_future(
        _publish(
            tenant_id=tenant_id,
            actor_id=actor_id,
            signal_kinds=signal_kinds,
            flagged_at=flagged_at,
        )
    )
    task.add_done_callback(lambda t: t.exception() if not t.cancelled() else None)
