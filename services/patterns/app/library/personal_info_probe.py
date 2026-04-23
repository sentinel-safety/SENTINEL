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
    r"\b(?:where do you live|what school|your address|home alone|"
    r"who (?:is|'?s) home|what'?s your (?:phone|number|address))\b",
    re.IGNORECASE,
)


class PersonalInfoProbePattern:
    name = "personal_info_probe"
    signal_kind = SignalKind.PERSONAL_INFO_PROBE
    mode = DetectionMode.RULE

    async def detect_sync(self, ctx: SyncPatternContext) -> tuple[PatternMatch, ...]:
        if not ctx.features.minor_recipient:
            return ()
        match = _PATTERN.search(ctx.features.normalized_content)
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
