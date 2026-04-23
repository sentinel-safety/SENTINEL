# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from shared.schemas.enums import EventType, ResponseTier
from shared.schemas.event import Event
from shared.schemas.suspicion_profile import SuspicionProfile
from shared.scoring.aggregator import apply_signals
from shared.scoring.signals import ScoreSignal, SignalKind

pytestmark = pytest.mark.unit


def _profile(now: datetime) -> SuspicionProfile:
    return SuspicionProfile(
        actor_id=uuid4(),
        tenant_id=uuid4(),
        current_score=20,
        tier=ResponseTier.WATCH,
        tier_entered_at=now,
        last_updated=now,
        last_decay_applied=now,
    )


def _event(tenant_id: UUID, actor_id: UUID, now: datetime) -> Event:
    return Event(
        id=uuid4(),
        tenant_id=tenant_id,
        conversation_id=uuid4(),
        actor_id=actor_id,
        timestamp=now,
        type=EventType.MESSAGE,
        content_hash="a" * 64,
    )


def test_grooming_stage_signal_stamps_marker() -> None:
    now = datetime(2026, 4, 19, 10, tzinfo=UTC)
    profile = _profile(now)
    event = _event(profile.tenant_id, profile.actor_id, now)
    outcome = apply_signals(
        profile=profile,
        signals=(ScoreSignal(kind=SignalKind.ISOLATION, confidence=1.0),),
        event=event,
        now=now,
    )
    assert f"last_qualifying_event={now.isoformat()}" in outcome.escalation_markers


def test_cross_session_signal_stamps_marker() -> None:
    now = datetime(2026, 4, 19, 10, tzinfo=UTC)
    profile = _profile(now)
    event = _event(profile.tenant_id, profile.actor_id, now)
    outcome = apply_signals(
        profile=profile,
        signals=(ScoreSignal(kind=SignalKind.CROSS_SESSION_ESCALATION, confidence=0.6),),
        event=event,
        now=now,
    )
    assert f"last_qualifying_event={now.isoformat()}" in outcome.escalation_markers


def test_non_qualifying_signal_does_not_stamp_marker() -> None:
    now = datetime(2026, 4, 19, 10, tzinfo=UTC)
    profile = _profile(now)
    event = _event(profile.tenant_id, profile.actor_id, now)
    outcome = apply_signals(
        profile=profile,
        signals=(ScoreSignal(kind=SignalKind.LATE_NIGHT_MINOR_CONTACT, confidence=1.0),),
        event=event,
        now=now,
    )
    assert outcome.escalation_markers == ()


def test_markers_tuple_contains_at_most_one_qualifying_entry() -> None:
    now = datetime(2026, 4, 19, 10, tzinfo=UTC)
    profile = _profile(now)
    event = _event(profile.tenant_id, profile.actor_id, now)
    outcome = apply_signals(
        profile=profile,
        signals=(
            ScoreSignal(kind=SignalKind.ISOLATION, confidence=1.0),
            ScoreSignal(kind=SignalKind.SEXUAL_ESCALATION, confidence=0.6),
        ),
        event=event,
        now=now,
    )
    qualifying = [m for m in outcome.escalation_markers if m.startswith("last_qualifying_event=")]
    assert len(qualifying) == 1
