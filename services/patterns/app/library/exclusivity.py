# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import re
from typing import Final

from shared.patterns import DetectionMode, PatternMatch, SyncPatternContext
from shared.scoring.signals import SignalKind

_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b(?:so mature for your age|not like other (?:kids|girls|boys)|"
    r"no one understands you like|you'?re special|our bond)\b",
    re.IGNORECASE,
)


class ExclusivityPattern:
    name = "exclusivity"
    signal_kind = SignalKind.EXCLUSIVITY
    mode = DetectionMode.RULE

    async def detect_sync(self, ctx: SyncPatternContext) -> tuple[PatternMatch, ...]:
        match = _PATTERN.search(ctx.features.normalized_content)
        if match is None:
            return ()
        matched = match.group(0)
        return (
            PatternMatch(
                pattern_name=self.name,
                signal_kind=self.signal_kind,
                confidence=0.85,
                evidence_excerpts=(matched,),
                detection_mode=self.mode,
                prompt_version=None,
                template_variables={"matched_phrase": matched},
            ),
        )
