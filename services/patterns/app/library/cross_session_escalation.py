# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from shared.patterns import DetectionMode, PatternMatch, SyncPatternContext
from shared.scoring.signals import SignalKind

_MIN_CONVERSATIONS = 3
_MIN_TARGETS = 2
_BASE_CONFIDENCE = 0.4
_STEP = 0.1
_MAX_CONFIDENCE = 0.9


class CrossSessionEscalationPattern:
    name = "cross_session_escalation"
    signal_kind = SignalKind.CROSS_SESSION_ESCALATION
    mode = DetectionMode.RULE

    async def detect_sync(self, ctx: SyncPatternContext) -> tuple[PatternMatch, ...]:
        memory = ctx.actor_memory
        if memory is None:
            return ()
        if not ctx.features.minor_recipient:
            return ()
        if memory.distinct_conversations_last_window < _MIN_CONVERSATIONS:
            return ()
        if memory.distinct_minor_targets_last_window < _MIN_TARGETS:
            return ()
        bonus = memory.distinct_conversations_last_window - _MIN_CONVERSATIONS
        confidence = min(_MAX_CONFIDENCE, _BASE_CONFIDENCE + _STEP * bonus)
        evidence = (
            f"actor contacted minors across {memory.distinct_conversations_last_window} "
            f"conversations with {memory.distinct_minor_targets_last_window} distinct targets "
            f"in last window",
        )
        return (
            PatternMatch(
                pattern_name=self.name,
                signal_kind=self.signal_kind,
                confidence=confidence,
                evidence_excerpts=evidence,
                detection_mode=self.mode,
                prompt_version=None,
                template_variables={
                    "conversations": memory.distinct_conversations_last_window,
                    "distinct_targets": memory.distinct_minor_targets_last_window,
                },
            ),
        )
