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


_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _profile() -> SuspicionProfile:
    return SuspicionProfile(
        actor_id=uuid4(),
        tenant_id=uuid4(),
        current_score=5,
        tier=ResponseTier.TRUSTED,
        tier_entered_at=_NOW,
        last_updated=_NOW,
        last_decay_applied=_NOW,
    )


def _event() -> Event:
    return Event(
        id=uuid4(),
        tenant_id=uuid4(),
        conversation_id=uuid4(),
        actor_id=uuid4(),
        timestamp=_NOW,
        type=EventType.MESSAGE,
        content_hash="a" * 64,
    )


def test_score_event_updates_score_and_returns_tier() -> None:
    outcome = score_event(
        profile=_profile(),
        signals=(ScoreSignal(kind=SignalKind.SECRECY_REQUEST, confidence=1.0),),
        event=_event(),
        now=_NOW,
    )
    assert outcome.new_score == 25
    assert outcome.previous_score == 5
    assert outcome.delta == 20
    assert outcome.new_tier is ResponseTier.WATCH


def test_score_event_no_signals_still_runs_decay() -> None:
    profile = SuspicionProfile(
        actor_id=uuid4(),
        tenant_id=uuid4(),
        current_score=30,
        tier=ResponseTier.WATCH,
        tier_entered_at=_NOW,
        last_updated=_NOW,
        last_decay_applied=_NOW,
    )
    outcome = score_event(
        profile=profile,
        signals=(),
        event=_event(),
        now=_NOW.replace(day=22),  # 21 days later
    )
    assert outcome.delta == -3
    assert outcome.new_score == 27


def test_tier_transition_flagged_when_crossed() -> None:
    profile = SuspicionProfile(
        actor_id=uuid4(),
        tenant_id=uuid4(),
        current_score=18,
        tier=ResponseTier.TRUSTED,
        tier_entered_at=_NOW,
        last_updated=_NOW,
        last_decay_applied=_NOW,
    )
    outcome = score_event(
        profile=profile,
        signals=(ScoreSignal(kind=SignalKind.ISOLATION, confidence=1.0),),
        event=_event(),
        now=_NOW,
    )
    assert outcome.previous_tier is ResponseTier.TRUSTED
    assert outcome.new_tier is ResponseTier.WATCH
    assert outcome.tier_changed is True
