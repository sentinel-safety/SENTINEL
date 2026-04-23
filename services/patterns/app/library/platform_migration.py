# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import re
from typing import Final

from shared.patterns import DetectionMode, PatternMatch, SyncPatternContext
from shared.scoring.signals import SignalKind

_PRIMARY: Final[re.Pattern[str]] = re.compile(
    r"\b(?:let'?s (?:move|continue|chat|talk)(?: (?:on|to))?|dm me on|add me on)\s+"
    r"(?:signal|whatsapp|telegram|discord|snap(?:chat)?|kik|wickr)\b",
    re.IGNORECASE,
)
_SECONDARY: Final[re.Pattern[str]] = re.compile(
    r"\bcontinue on (?:signal|whatsapp|telegram|discord|snap(?:chat)?|kik|wickr)\b",
    re.IGNORECASE,
)


class PlatformMigrationPattern:
    name = "platform_migration"
    signal_kind = SignalKind.PLATFORM_MIGRATION_REQUEST
    mode = DetectionMode.RULE

    async def detect_sync(self, ctx: SyncPatternContext) -> tuple[PatternMatch, ...]:
        text = ctx.features.normalized_content
        match = _PRIMARY.search(text) or _SECONDARY.search(text)
        if match is None:
            return ()
        matched = match.group(0)
        return (
            PatternMatch(
                pattern_name=self.name,
                signal_kind=self.signal_kind,
                confidence=1.0,
                evidence_excerpts=(matched,),
                detection_mode=self.mode,
                prompt_version=None,
                template_variables={"matched_phrase": matched},
            ),
        )
