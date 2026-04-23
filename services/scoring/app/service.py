# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import datetime

from shared.schemas.base import FrozenModel
from shared.schemas.enums import ResponseTier
from shared.schemas.event import Event
from shared.schemas.suspicion_profile import ScoreHistoryEntry, SuspicionProfile
from shared.scoring.aggregator import apply_signals
from shared.scoring.decay import apply_decay
from shared.scoring.signals import ScoreSignal
from shared.scoring.tier import tier_for_score


class ScoringOutcome(FrozenModel):
    profile: SuspicionProfile
    previous_score: int
    new_score: int
    delta: int
    previous_tier: ResponseTier
    new_tier: ResponseTier
    tier_changed: bool
    history_entries: tuple[ScoreHistoryEntry, ...]


def score_event(
    *,
    profile: SuspicionProfile,
    signals: tuple[ScoreSignal, ...],
    event: Event,
    now: datetime,
) -> ScoringOutcome:
    previous_score = profile.current_score
    previous_tier = profile.tier

    decay = apply_decay(profile, now=now)
    decayed_history: tuple[ScoreHistoryEntry, ...] = ()
    running_score = decay.new_score
    last_decay_applied = decay.last_decay_applied
    if decay.delta != 0:
        decayed_history = (
            ScoreHistoryEntry(
                at=now,
                delta=decay.delta,
                cause="decay",
                new_score=decay.new_score,
            ),
        )

    interim = profile.model_copy(
        update={
            "current_score": running_score,
            "last_decay_applied": last_decay_applied,
            "last_updated": now,
        }
    )
    aggregation = apply_signals(profile=interim, signals=signals, event=event, now=now)
    new_score = aggregation.new_score
    new_tier = tier_for_score(new_score)
    tier_changed = new_tier != previous_tier
    tier_entered_at = now if tier_changed else profile.tier_entered_at

    updated = interim.model_copy(
        update={
            "current_score": new_score,
            "tier": new_tier,
            "tier_entered_at": tier_entered_at,
            "last_updated": now,
            "escalation_markers": aggregation.escalation_markers,
        }
    )
    history = decayed_history + aggregation.history_entries
    return ScoringOutcome(
        profile=updated,
        previous_score=previous_score,
        new_score=new_score,
        delta=new_score - previous_score,
        previous_tier=previous_tier,
        new_tier=new_tier,
        tier_changed=tier_changed,
        history_entries=history,
    )
