# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from services.scoring.app.service import score_event
from shared.schemas.enums import EventType, ResponseTier
from shared.schemas.event import Event
from shared.schemas.suspicion_profile import SuspicionProfile
from shared.scoring.signals import ScoreSignal, SignalKind

pytestmark = pytest.mark.unit


def _profile(now: datetime) -> SuspicionProfile:
    return SuspicionProfile(
        actor_id=uuid4(),
        tenant_id=uuid4(),
        current_score=10,
        tier=ResponseTier.TRUSTED,
        tier_entered_at=now,
        last_updated=now,
        last_decay_applied=now,
    )


def _event(profile: SuspicionProfile, now: datetime) -> Event:
    return Event(
        id=uuid4(),
        tenant_id=profile.tenant_id,
        conversation_id=uuid4(),
        actor_id=profile.actor_id,
        timestamp=now,
        type=EventType.MESSAGE,
        content_hash="b" * 64,
    )


def test_qualifying_signal_produces_profile_with_marker() -> None:
    now = datetime(2026, 4, 19, 9, tzinfo=UTC)
    profile = _profile(now)
    outcome = score_event(
        profile=profile,
        signals=(ScoreSignal(kind=SignalKind.ISOLATION, confidence=1.0),),
        event=_event(profile, now),
        now=now,
    )
    markers = outcome.profile.escalation_markers
    assert any(m == f"last_qualifying_event={now.isoformat()}" for m in markers)


def test_non_qualifying_signal_leaves_markers_empty() -> None:
    now = datetime(2026, 4, 19, 9, tzinfo=UTC)
    profile = _profile(now)
    outcome = score_event(
        profile=profile,
        signals=(ScoreSignal(kind=SignalKind.LATE_NIGHT_MINOR_CONTACT, confidence=1.0),),
        event=_event(profile, now),
        now=now,
    )
    assert all(
        not m.startswith("last_qualifying_event=") for m in outcome.profile.escalation_markers
    )


def test_second_qualifying_signal_replaces_older_marker() -> None:
    earlier = datetime(2026, 4, 1, 9, tzinfo=UTC)
    later = datetime(2026, 4, 19, 9, tzinfo=UTC)
    seed = _profile(earlier)
    seeded = seed.model_copy(
        update={"escalation_markers": (f"last_qualifying_event={earlier.isoformat()}",)}
    )
    outcome = score_event(
        profile=seeded,
        signals=(ScoreSignal(kind=SignalKind.DESENSITIZATION, confidence=0.8),),
        event=_event(seeded, later),
        now=later,
    )
    qualifying = [
        m for m in outcome.profile.escalation_markers if m.startswith("last_qualifying_event=")
    ]
    assert qualifying == [f"last_qualifying_event={later.isoformat()}"]
