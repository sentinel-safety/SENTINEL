# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from shared.patterns.matches import DetectionMode, PatternMatch
from shared.patterns.protocol import SyncPatternContext
from shared.scoring.signals import SignalKind


class AgeIncongruencePattern:
    name = "age_incongruence"
    signal_kind = SignalKind.RAPID_ESCALATION
    mode = DetectionMode.RULE

    async def detect_sync(self, ctx: SyncPatternContext) -> tuple[PatternMatch, ...]:
        return ()
