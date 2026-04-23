# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import logging

import httpx

from shared.response.tier_change import TierChangeEvent

_log = logging.getLogger(__name__)


async def _post_evaluate(base_url: str, payload: dict[str, object]) -> None:
    async with httpx.AsyncClient(timeout=5.0) as client:
        await client.post(f"{base_url}/internal/honeypot/evaluate", json=payload)


async def maybe_dispatch_honeypot(
    *,
    event: TierChangeEvent,
    base_url: str,
    tier_threshold: int,
) -> None:
    if int(event.new_tier) < tier_threshold:
        return
    payload = {
        "tenant_id": str(event.tenant_id),
        "actor_id": str(event.actor_id),
        "actor_tier": int(event.new_tier),
        "persona_id": "emma-13-us-east",
        "conversation_excerpt": [],
        "pattern_matches": [],
        "reasoning_snapshot": {},
    }
    try:
        await _post_evaluate(base_url, payload)
    except httpx.HTTPError as exc:  # pragma: no cover - network resilience
        _log.warning("honeypot dispatch failed: %s", exc)
