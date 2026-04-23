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


def _profile(score: int, *, last_updated: datetime, markers: tuple[str, ...]) -> SuspicionProfile:
    return SuspicionProfile(
        actor_id=uuid4(),
        tenant_id=uuid4(),
        current_score=score,
        tier=ResponseTier.ACTIVE_MONITOR,
        tier_entered_at=last_updated,
        last_updated=last_updated,
        last_decay_applied=last_updated,
        escalation_markers=markers,
    )


def test_marker_within_30_days_suspends_decay_after_28_days() -> None:
    start = datetime(2026, 4, 1, 12, tzinfo=UTC)
    profile = _profile(
        40,
        last_updated=start,
        markers=(f"last_qualifying_event={start.isoformat()}",),
    )
    later = start + timedelta(days=28)
    outcome = apply_decay(profile, now=later)
    assert outcome.delta == 0
    assert outcome.new_score == 40


def test_marker_older_than_30_days_allows_decay() -> None:
    start = datetime(2026, 2, 1, 12, tzinfo=UTC)
    profile = _profile(
        40,
        last_updated=start,
        markers=(f"last_qualifying_event={start.isoformat()}",),
    )
    later = start + timedelta(days=45)
    outcome = apply_decay(profile, now=later)
    assert outcome.delta < 0


def test_no_marker_allows_decay_after_window() -> None:
    start = datetime(2026, 2, 1, 12, tzinfo=UTC)
    profile = _profile(30, last_updated=start, markers=())
    later = start + timedelta(days=15)
    outcome = apply_decay(profile, now=later)
    assert outcome.delta < 0
