# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import datetime, timedelta

from pydantic import Field

from shared.schemas.base import FrozenModel, UtcDatetime
from shared.schemas.enums import ResponseTier
from shared.schemas.suspicion_profile import SuspicionProfile

_DECAY_FLOOR: int = 5
_DECAY_WINDOW_DAYS: int = 7
_SUSPENSION_WINDOW_DAYS: int = 30
_MARKER_PREFIX: str = "last_qualifying_event="


class DecayOutcome(FrozenModel):
    new_score: int = Field(ge=0, le=100)
    delta: int
    last_decay_applied: UtcDatetime


def _decay_interval_days(tier: ResponseTier) -> int:
    if tier in {ResponseTier.THROTTLE, ResponseTier.RESTRICT, ResponseTier.CRITICAL}:
        return _DECAY_WINDOW_DAYS * 2
    return _DECAY_WINDOW_DAYS


def _last_qualifying_event(profile: SuspicionProfile) -> datetime | None:
    for marker in profile.escalation_markers:
        if marker.startswith(_MARKER_PREFIX):
            return datetime.fromisoformat(marker[len(_MARKER_PREFIX) :])
    return None


def apply_decay(profile: SuspicionProfile, *, now: datetime) -> DecayOutcome:
    last = profile.last_decay_applied or profile.last_updated
    elapsed_days = (now - last).days

    qualifying = _last_qualifying_event(profile)
    if qualifying is not None and (now - qualifying).days < _SUSPENSION_WINDOW_DAYS:
        return DecayOutcome(new_score=profile.current_score, delta=0, last_decay_applied=last)

    interval = _decay_interval_days(profile.tier)
    points = elapsed_days // interval
    if points <= 0 or profile.current_score <= _DECAY_FLOOR:
        return DecayOutcome(new_score=profile.current_score, delta=0, last_decay_applied=last)

    target = max(_DECAY_FLOOR, profile.current_score - points)
    delta = target - profile.current_score
    applied_at = last + timedelta(days=points * interval)
    return DecayOutcome(new_score=target, delta=delta, last_decay_applied=applied_at)
