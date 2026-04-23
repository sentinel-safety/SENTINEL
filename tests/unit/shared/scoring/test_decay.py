# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from shared.schemas.enums import ResponseTier
from shared.schemas.suspicion_profile import SuspicionProfile
from shared.scoring.decay import apply_decay

pytestmark = pytest.mark.unit

_BASE_TIME = datetime(2026, 1, 1, tzinfo=UTC)


def _profile(
    *,
    score: int,
    tier: ResponseTier,
    last_decay: datetime,
    last_qualifying_event: datetime | None = None,
) -> SuspicionProfile:
    markers: tuple[str, ...] = ()
    if last_qualifying_event is not None:
        markers = (f"last_qualifying_event={last_qualifying_event.isoformat()}",)
    return SuspicionProfile(
        actor_id=uuid4(),
        tenant_id=uuid4(),
        current_score=score,
        tier=tier,
        tier_entered_at=_BASE_TIME,
        last_updated=last_decay,
        last_decay_applied=last_decay,
        escalation_markers=markers,
    )


def test_decay_drops_one_point_per_seven_days_below_tier_three() -> None:
    profile = _profile(score=30, tier=ResponseTier.WATCH, last_decay=_BASE_TIME)
    outcome = apply_decay(profile, now=_BASE_TIME + timedelta(days=21))
    assert outcome.delta == -3
    assert outcome.new_score == 27


def test_decay_halved_at_or_above_tier_three() -> None:
    profile = _profile(score=70, tier=ResponseTier.THROTTLE, last_decay=_BASE_TIME)
    outcome = apply_decay(profile, now=_BASE_TIME + timedelta(days=28))
    assert outcome.delta == -2
    assert outcome.new_score == 68


def test_decay_floor_of_five() -> None:
    profile = _profile(score=6, tier=ResponseTier.TRUSTED, last_decay=_BASE_TIME)
    outcome = apply_decay(profile, now=_BASE_TIME + timedelta(days=70))
    assert outcome.new_score == 5
    assert outcome.delta == -1


def test_decay_noop_when_insufficient_time() -> None:
    profile = _profile(score=30, tier=ResponseTier.WATCH, last_decay=_BASE_TIME)
    outcome = apply_decay(profile, now=_BASE_TIME + timedelta(days=5))
    assert outcome.delta == 0
    assert outcome.new_score == 30


def test_decay_suspended_by_recent_qualifying_event() -> None:
    profile = _profile(
        score=50,
        tier=ResponseTier.ACTIVE_MONITOR,
        last_decay=_BASE_TIME,
        last_qualifying_event=_BASE_TIME + timedelta(days=10),
    )
    outcome = apply_decay(profile, now=_BASE_TIME + timedelta(days=30))
    assert outcome.delta == 0
    assert outcome.new_score == 50
