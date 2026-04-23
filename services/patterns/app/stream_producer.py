# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import orjson
import redis.asyncio as aioredis

from shared.contracts.patterns import DetectRequest


async def enqueue_for_llm(
    redis: aioredis.Redis,  # type: ignore[type-arg]
    *,
    queue_name: str,
    request: DetectRequest,
) -> None:
    payload = orjson.dumps(request.model_dump(mode="json"))
    await redis.xadd(queue_name, {"data": payload})
