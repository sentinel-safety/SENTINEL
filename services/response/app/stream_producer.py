# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import orjson
import redis.asyncio as aioredis

from shared.response.tier_change import TierChangeEvent


async def enqueue_tier_change(
    redis: aioredis.Redis,  # type: ignore[type-arg]
    *,
    stream_name: str,
    event: TierChangeEvent,
) -> None:
    payload = orjson.dumps(event.model_dump(mode="json"))
    await redis.xadd(stream_name, {"data": payload})
