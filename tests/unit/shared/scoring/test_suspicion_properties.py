# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from shared.schemas.enums import EventType, ResponseTier
from shared.schemas.event import Event
from shared.schemas.suspicion_profile import SuspicionProfile
from shared.scoring.aggregator import apply_signals
from shared.scoring.decay import apply_decay
from shared.scoring.deltas import DELTA_BY_SIGNAL
from shared.scoring.signals import ScoreSignal, SignalKind
from shared.scoring.tier import tier_for_score

pytestmark = pytest.mark.unit


def _profile(score: int, now: datetime) -> SuspicionProfile:
    return SuspicionProfile(
        actor_id=uuid4(),
        tenant_id=uuid4(),
        current_score=score,
        tier=tier_for_score(score),
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
        content_hash="a" * 64,
    )


@given(score=st.integers(min_value=0, max_value=100))
def test_tier_mapping_is_monotonic(score: int) -> None:
    tier = tier_for_score(score)
    assert isinstance(tier, ResponseTier)
    if score < 100:
        next_tier = tier_for_score(score + 1)
        assert int(next_tier) >= int(tier)


@given(
    score=st.integers(min_value=0, max_value=100),
    kind=st.sampled_from(list(SignalKind)),
    confidence=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=200)
def test_score_clamps_to_valid_range(score: int, kind: SignalKind, confidence: float) -> None:
    now = datetime.now(UTC)
    profile = _profile(score, now)
    outcome = apply_signals(
        profile=profile,
        signals=(ScoreSignal(kind=kind, confidence=confidence, evidence="x"),),
        event=_event(profile, now),
        now=now,
    )
    assert 0 <= outcome.new_score <= 100


@given(
    score=st.integers(min_value=0, max_value=100),
    days=st.integers(min_value=0, max_value=365),
)
@settings(max_examples=200)
def test_decay_never_goes_below_zero(score: int, days: int) -> None:
    now = datetime.now(UTC)
    past = now - timedelta(days=days)
    profile = _profile(score, past)
    decayed = apply_decay(profile=profile, now=now)
    assert decayed.new_score >= 0
    assert decayed.new_score <= 100


@given(
    score=st.integers(min_value=0, max_value=100),
    days=st.integers(min_value=0, max_value=365),
)
@settings(max_examples=200)
def test_decay_is_monotonic_non_increasing(score: int, days: int) -> None:
    now = datetime.now(UTC)
    past = now - timedelta(days=days)
    profile = _profile(score, past)
    decayed = apply_decay(profile=profile, now=now)
    assert decayed.new_score <= score


def test_every_signal_kind_has_delta() -> None:
    for kind in SignalKind:
        assert kind in DELTA_BY_SIGNAL, f"no delta for {kind}"
        assert isinstance(DELTA_BY_SIGNAL[kind], int)


@given(score=st.integers(min_value=0, max_value=100))
def test_tier_thresholds_cover_entire_range(score: int) -> None:
    tier = tier_for_score(score)
    assert tier in ResponseTier
