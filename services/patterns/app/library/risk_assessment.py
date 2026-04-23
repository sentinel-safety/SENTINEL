# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Final

from services.patterns.app.prompts.loader import load_prompt
from shared.llm.provider import LLMCallError, LLMProvider
from shared.patterns.matches import DetectionMode, PatternMatch
from shared.patterns.protocol import LLMPatternContext
from shared.scoring.signals import SignalKind

_PROMPT_VERSION: Final = "v1"
_CONFIDENCE_THRESHOLD: Final = 0.55

_RESPONSE_SCHEMA: Final[dict[str, Any]] = {
    "type": "object",
    "properties": {
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "evidence_excerpts": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 3,
        },
    },
    "required": ["confidence", "evidence_excerpts"],
    "additionalProperties": False,
}


@dataclass
class RiskAssessmentPattern:
    provider: LLMProvider
    _prompt_template: str = field(init=False)

    name = "risk_assessment"
    signal_kind = SignalKind.RISK_ASSESSMENT
    mode = DetectionMode.LLM

    def __post_init__(self) -> None:
        self._prompt_template = load_prompt(self.name, _PROMPT_VERSION)

    def _render_prompt(self, message: str, history: tuple[str, ...]) -> str:
        history_text = "\n".join(history) if history else "(none)"
        return self._prompt_template.replace("{{message}}", message).replace(
            "{{history}}", history_text
        )

    async def detect_llm(self, ctx: LLMPatternContext) -> tuple[PatternMatch, ...]:
        if not ctx.features.minor_recipient:
            return ()
        prompt = self._render_prompt(ctx.features.normalized_content, ctx.recent_messages)
        try:
            result = await self.provider.complete(prompt=prompt, schema=_RESPONSE_SCHEMA)
        except LLMCallError:
            return ()
        confidence: float = result["confidence"]
        if confidence < _CONFIDENCE_THRESHOLD:
            return ()
        excerpts: tuple[str, ...] = tuple(result.get("evidence_excerpts", []))
        excerpt = excerpts[0] if excerpts else ""
        return (
            PatternMatch(
                pattern_name=self.name,
                signal_kind=self.signal_kind,
                confidence=confidence,
                evidence_excerpts=excerpts,
                detection_mode=self.mode,
                prompt_version=_PROMPT_VERSION,
                template_variables={
                    "confidence": round(confidence, 2),
                    "excerpt": excerpt,
                },
            ),
        )
