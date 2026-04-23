# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from shared.config import get_settings
from shared.patterns.matches import DetectionMode, PatternMatch
from shared.patterns.protocol import SyncPatternContext
from shared.scoring.signals import SignalKind


class BehavioralFingerprintMatchPattern:
    name = "behavioral_fingerprint_match"
    signal_kind = SignalKind.BEHAVIORAL_FINGERPRINT_MATCH
    mode = DetectionMode.RULE

    async def detect_sync(self, ctx: SyncPatternContext) -> tuple[PatternMatch, ...]:
        threshold = get_settings().fingerprint_similarity_threshold
        flagged = tuple(n for n in ctx.fingerprint_neighbors if n.flagged and n.score >= threshold)
        if not flagged:
            return ()
        best = max(flagged, key=lambda n: n.score)
        return (
            PatternMatch(
                pattern_name=self.name,
                signal_kind=self.signal_kind,
                confidence=best.score,
                evidence_excerpts=(
                    f"fingerprint cosine similarity {best.score:.3f} to flagged actor "
                    f"{best.actor_id}",
                ),
                detection_mode=self.mode,
                prompt_version=None,
                template_variables={"similarity": round(best.score, 2)},
            ),
        )
