# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from shared.response.tier_change import TierChangeEvent
from shared.schemas.enums import ResponseTier

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


def _event(previous: ResponseTier, new: ResponseTier, score: int) -> TierChangeEvent:
    return TierChangeEvent(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        event_id=uuid4(),
        previous_tier=previous,
        new_tier=new,
        new_score=score,
        triggered_at=datetime.now(UTC),
        reasoning=None,
    )


async def test_scoring_fires_honeypot_when_tier_reaches_threshold() -> None:
    from services.scoring.app.honeypot_dispatch import maybe_dispatch_honeypot

    called = AsyncMock()
    with patch("services.scoring.app.honeypot_dispatch._post_evaluate", called):
        await maybe_dispatch_honeypot(
            event=_event(ResponseTier.THROTTLE, ResponseTier.RESTRICT, 75),
            base_url="http://127.0.0.1:8010",
            tier_threshold=4,
        )
    called.assert_awaited_once()


async def test_scoring_does_not_fire_when_below_threshold() -> None:
    from services.scoring.app.honeypot_dispatch import maybe_dispatch_honeypot

    called = AsyncMock()
    with patch("services.scoring.app.honeypot_dispatch._post_evaluate", called):
        await maybe_dispatch_honeypot(
            event=_event(ResponseTier.ACTIVE_MONITOR, ResponseTier.THROTTLE, 60),
            base_url="http://127.0.0.1:8010",
            tier_threshold=4,
        )
    called.assert_not_awaited()
