# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from shared.response.tier_change import TierChangeEvent
from shared.schemas.enums import ResponseTier
from shared.schemas.reasoning import PrimaryDriver, Reasoning

pytestmark = pytest.mark.unit


def _reasoning(tenant: uuid.UUID, actor: uuid.UUID) -> Reasoning:
    return Reasoning(
        actor_id=actor,
        tenant_id=tenant,
        score_change=18,
        new_score=64,
        new_tier=ResponseTier.THROTTLE,
        primary_drivers=(
            PrimaryDriver(
                pattern="Platform Migration Request",
                pattern_id="platform_migration",
                confidence=0.91,
                evidence="Actor asked to move to Telegram.",
            ),
        ),
        generated_at=datetime.now(UTC),
    )


def test_reasoning_defaults_to_none() -> None:
    evt = TierChangeEvent(
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        event_id=uuid.uuid4(),
        previous_tier=ResponseTier.ACTIVE_MONITOR,
        new_tier=ResponseTier.THROTTLE,
        new_score=64,
        triggered_at=datetime.now(UTC),
    )
    assert evt.reasoning is None


def test_reasoning_round_trips_through_redis_shape() -> None:
    tid = uuid.uuid4()
    aid = uuid.uuid4()
    evt = TierChangeEvent(
        tenant_id=tid,
        actor_id=aid,
        event_id=uuid.uuid4(),
        previous_tier=ResponseTier.ACTIVE_MONITOR,
        new_tier=ResponseTier.THROTTLE,
        new_score=64,
        triggered_at=datetime.now(UTC),
        reasoning=_reasoning(tid, aid),
    )
    restored = TierChangeEvent.model_validate(evt.model_dump(mode="json"))
    assert restored.reasoning == evt.reasoning
