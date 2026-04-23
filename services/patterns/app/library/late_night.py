# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from shared.patterns import DetectionMode, PatternMatch, SyncPatternContext
from shared.scoring.signals import SignalKind


class LateNightPattern:
    name = "late_night"
    signal_kind = SignalKind.LATE_NIGHT_MINOR_CONTACT
    mode = DetectionMode.RULE

    async def detect_sync(self, ctx: SyncPatternContext) -> tuple[PatternMatch, ...]:
        if not (ctx.features.minor_recipient and ctx.features.late_night_local):
            return ()
        return (
            PatternMatch(
                pattern_name=self.name,
                signal_kind=self.signal_kind,
                confidence=1.0,
                evidence_excerpts=("late-night contact with minor (local time)",),
                detection_mode=self.mode,
                prompt_version=None,
                template_variables={},
            ),
        )
