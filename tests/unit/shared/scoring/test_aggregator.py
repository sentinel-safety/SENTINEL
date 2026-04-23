# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from shared.schemas.enums import EventType, ResponseTier
from shared.schemas.event import Event
from shared.schemas.suspicion_profile import SuspicionProfile
from shared.scoring.aggregator import apply_signals
from shared.scoring.signals import ScoreSignal, SignalKind

pytestmark = pytest.mark.unit

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _profile(score: int = 5) -> SuspicionProfile:
    return SuspicionProfile(
        actor_id=uuid4(),
        tenant_id=uuid4(),
        current_score=score,
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
        target_actor_ids=(),
        timestamp=_NOW,
        type=EventType.MESSAGE,
        content_hash="a" * 64,
    )


def test_single_signal_increments_score_by_delta_times_confidence() -> None:
    profile = _profile(score=10)
    signals = (ScoreSignal(kind=SignalKind.SECRECY_REQUEST, confidence=1.0),)
    outcome = apply_signals(profile=profile, signals=signals, event=_event(), now=_NOW)
    assert outcome.delta == 20
    assert outcome.new_score == 30
    assert len(outcome.history_entries) == 1
    assert outcome.history_entries[0].cause == "signal:secrecy_request"


def test_clamps_to_ceiling() -> None:
    profile = _profile(score=95)
    signals = (ScoreSignal(kind=SignalKind.SEXUAL_ESCALATION, confidence=1.0),)
    outcome = apply_signals(profile=profile, signals=signals, event=_event(), now=_NOW)
    assert outcome.new_score == 100
    assert outcome.delta == 5


def test_clamps_to_floor() -> None:
    profile = _profile(score=2)
    signals = (ScoreSignal(kind=SignalKind.CLEAN_REVIEW, confidence=1.0),)
    outcome = apply_signals(profile=profile, signals=signals, event=_event(), now=_NOW)
    assert outcome.new_score == 0
    assert outcome.delta == -2


def test_confidence_scales_contribution() -> None:
    profile = _profile(score=10)
    signals = (ScoreSignal(kind=SignalKind.GIFT_OFFERING, confidence=0.5),)
    outcome = apply_signals(profile=profile, signals=signals, event=_event(), now=_NOW)
    assert outcome.delta == 6
    assert outcome.new_score == 16


def test_multiple_signals_sum_in_deterministic_order() -> None:
    profile = _profile(score=5)
    signals = (
        ScoreSignal(kind=SignalKind.ISOLATION, confidence=1.0),
        ScoreSignal(kind=SignalKind.SECRECY_REQUEST, confidence=1.0),
    )
    outcome = apply_signals(profile=profile, signals=signals, event=_event(), now=_NOW)
    assert outcome.delta == 32
    assert outcome.new_score == 37
    assert [entry.cause for entry in outcome.history_entries] == [
        "signal:isolation",
        "signal:secrecy_request",
    ]


def test_no_signals_noop() -> None:
    profile = _profile(score=42)
    outcome = apply_signals(profile=profile, signals=(), event=_event(), now=_NOW)
    assert outcome.delta == 0
    assert outcome.new_score == 42
    assert outcome.history_entries == ()
