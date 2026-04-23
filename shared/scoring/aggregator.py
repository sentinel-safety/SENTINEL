# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import datetime

from shared.schemas.base import FrozenModel
from shared.schemas.enums import GroomingStage
from shared.schemas.event import Event
from shared.schemas.suspicion_profile import ScoreHistoryEntry, SuspicionProfile
from shared.scoring.deltas import DELTA_BY_SIGNAL
from shared.scoring.signals import ScoreSignal, SignalKind

_MARKER_PREFIX = "last_qualifying_event="
_GROOMING_STAGE_VALUES = frozenset(stage.value for stage in GroomingStage)


class AggregationOutcome(FrozenModel):
    new_score: int
    delta: int
    history_entries: tuple[ScoreHistoryEntry, ...]
    escalation_markers: tuple[str, ...] = ()


def _round_toward_zero(value: float) -> int:
    if value >= 0:
        return int(value)
    return -int(-value)


def _is_qualifying(kind: SignalKind) -> bool:
    if kind in {
        SignalKind.CROSS_SESSION_ESCALATION,
        SignalKind.MULTI_MINOR_CONTACT_WINDOW,
        SignalKind.BEHAVIORAL_FINGERPRINT_MATCH,
        SignalKind.SUSPICIOUS_CLUSTER_MEMBERSHIP,
        SignalKind.FEDERATION_SIGNAL_MATCH,
    }:
        return True
    return kind.value in _GROOMING_STAGE_VALUES


def apply_signals(
    *,
    profile: SuspicionProfile,
    signals: tuple[ScoreSignal, ...],
    event: Event,
    now: datetime,
) -> AggregationOutcome:
    running_score = profile.current_score
    entries: list[ScoreHistoryEntry] = []
    total_delta = 0
    qualifying_seen = False

    for signal in signals:
        weighted = DELTA_BY_SIGNAL[signal.kind] * signal.confidence
        per_signal_delta = _round_toward_zero(weighted)
        next_score = max(0, min(100, running_score + per_signal_delta))
        actual_delta = next_score - running_score
        if actual_delta == 0:
            continue
        entries.append(
            ScoreHistoryEntry(
                at=now,
                delta=actual_delta,
                cause=f"signal:{signal.kind.value}",
                new_score=next_score,
                source_event_id=event.id,
            )
        )
        running_score = next_score
        total_delta += actual_delta
        if _is_qualifying(signal.kind):
            qualifying_seen = True

    existing = tuple(m for m in profile.escalation_markers if not m.startswith(_MARKER_PREFIX))
    markers: tuple[str, ...] = existing
    if qualifying_seen:
        markers = (*existing, f"{_MARKER_PREFIX}{now.isoformat()}")

    return AggregationOutcome(
        new_score=running_score,
        delta=total_delta,
        history_entries=tuple(entries),
        escalation_markers=markers,
    )
