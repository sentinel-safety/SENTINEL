# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from typing import Final

from shared.config import get_settings
from shared.patterns.matches import DetectionMode, PatternMatch
from shared.patterns.protocol import SyncPatternContext
from shared.scoring.signals import SignalKind

_BASE: Final[float] = 0.6
_STEP: Final[float] = 0.05
_MAX: Final[float] = 0.95


class SuspiciousClusterMembershipPattern:
    name = "suspicious_cluster_membership"
    signal_kind = SignalKind.SUSPICIOUS_CLUSTER_MEMBERSHIP
    mode = DetectionMode.RULE

    async def detect_sync(self, ctx: SyncPatternContext) -> tuple[PatternMatch, ...]:
        settings = get_settings()
        threshold = settings.fingerprint_similarity_threshold
        min_flagged = settings.cluster_min_flagged_neighbors
        qualifying = tuple(
            n for n in ctx.fingerprint_neighbors if n.flagged and n.score >= threshold
        )
        if len(qualifying) < min_flagged:
            return ()
        bonus = len(qualifying) - min_flagged
        confidence = min(_MAX, _BASE + _STEP * bonus)
        return (
            PatternMatch(
                pattern_name=self.name,
                signal_kind=self.signal_kind,
                confidence=confidence,
                evidence_excerpts=(
                    f"{len(qualifying)} flagged fingerprint neighbors above "
                    f"{threshold:.2f} similarity",
                ),
                detection_mode=self.mode,
                prompt_version=None,
                template_variables={
                    "flagged_neighbors": len(qualifying),
                    "threshold": round(threshold, 2),
                },
            ),
        )
