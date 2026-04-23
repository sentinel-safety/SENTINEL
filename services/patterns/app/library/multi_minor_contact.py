# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from typing import Final

from shared.patterns import DetectionMode, PatternMatch, SyncPatternContext
from shared.scoring.signals import SignalKind

_THRESHOLD: Final[int] = 3
_BASE: Final[float] = 0.5
_STEP: Final[float] = 0.05
_MAX: Final[float] = 0.95


class MultiMinorContactPattern:
    name = "multi_minor_contact"
    signal_kind = SignalKind.MULTI_MINOR_CONTACT_WINDOW
    mode = DetectionMode.RULE

    async def detect_sync(self, ctx: SyncPatternContext) -> tuple[PatternMatch, ...]:
        graph = ctx.contact_graph
        if graph is None:
            return ()
        if graph.distinct_minor_contacts_window < _THRESHOLD:
            return ()
        bonus = graph.distinct_minor_contacts_window - _THRESHOLD
        confidence = min(_MAX, _BASE + _STEP * bonus)
        return (
            PatternMatch(
                pattern_name=self.name,
                signal_kind=self.signal_kind,
                confidence=confidence,
                evidence_excerpts=(
                    f"{graph.distinct_minor_contacts_window} distinct minor contacts in "
                    f"last {graph.lookback_days}d "
                    f"(velocity {graph.contact_velocity_per_day:.2f}/day)",
                ),
                detection_mode=self.mode,
                prompt_version=None,
                template_variables={
                    "distinct_minors": graph.distinct_minor_contacts_window,
                    "lookback_days": graph.lookback_days,
                    "velocity_per_day": round(graph.contact_velocity_per_day, 2),
                },
            ),
        )
