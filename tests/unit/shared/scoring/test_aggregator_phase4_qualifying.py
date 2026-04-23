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


@pytest.mark.parametrize(
    "kind",
    [
        SignalKind.MULTI_MINOR_CONTACT_WINDOW,
        SignalKind.BEHAVIORAL_FINGERPRINT_MATCH,
        SignalKind.SUSPICIOUS_CLUSTER_MEMBERSHIP,
    ],
)
def test_phase4_signal_stamps_marker(kind: SignalKind) -> None:
    now = datetime(2026, 4, 19, 10, tzinfo=UTC)
    profile = _profile(now)
    outcome = apply_signals(
        profile=profile,
        signals=(ScoreSignal(kind=kind, confidence=1.0),),
        event=_event(profile, now),
        now=now,
    )
    assert f"last_qualifying_event={now.isoformat()}" in outcome.escalation_markers
