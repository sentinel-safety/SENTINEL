# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from enum import StrEnum

from pydantic import Field, model_validator

from shared.schemas.base import FrozenModel
from shared.scoring.signals import SignalKind


class DetectionMode(StrEnum):
    RULE = "rule"
    LLM = "llm"


class PatternMatch(FrozenModel):
    pattern_name: str = Field(min_length=1, max_length=64)
    signal_kind: SignalKind
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_excerpts: tuple[str, ...] = Field(default_factory=tuple)
    detection_mode: DetectionMode
    prompt_version: str | None = None
    template_variables: dict[str, str | int | float | bool] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_prompt_version_matches_mode(self) -> PatternMatch:
        if self.detection_mode is DetectionMode.LLM and self.prompt_version is None:
            raise ValueError("LLM detection requires prompt_version")
        if self.detection_mode is DetectionMode.RULE and self.prompt_version is not None:
            raise ValueError("rule detection must not carry prompt_version")
        return self
