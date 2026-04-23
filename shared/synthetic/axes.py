# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, model_validator

from shared.schemas.base import FrozenModel


class GroomingStage(StrEnum):
    FRIENDSHIP_FORMING = "friendship_forming"
    RISK_ASSESSMENT = "risk_assessment"
    EXCLUSIVITY = "exclusivity"
    ISOLATION = "isolation"
    DESENSITIZATION = "desensitization"
    SEXUAL_ESCALATION = "sexual_escalation"


class Platform(StrEnum):
    DM = "dm"
    GROUP_CHAT = "group_chat"
    GAME_CHAT = "game_chat"
    FORUM_PM = "forum_pm"
    VOICE_TRANSCRIPT = "voice_transcript"


class CommunicationStyle(StrEnum):
    CASUAL_TYPING = "casual_typing"
    FORMAL = "formal"
    EMOJI_HEAVY = "emoji_heavy"
    INTERNET_SLANG = "internet_slang"
    REGIONAL_COLLOQUIAL = "regional_colloquial"


class Demographics(FrozenModel):
    age_band: Literal["11-13", "14-15", "16-17"]
    gender: str
    regional_context: str


class DiversityAxes(FrozenModel):
    demographics: Annotated[tuple[Demographics, ...], Field(min_length=1)]
    platforms: Annotated[tuple[Platform, ...], Field(min_length=1)]
    communication_styles: Annotated[tuple[CommunicationStyle, ...], Field(min_length=1)]
    languages: Annotated[tuple[str, ...], Field(min_length=1)]


class StageMix(FrozenModel):
    weights: dict[GroomingStage, int]

    @model_validator(mode="after")
    def _weights_sum_nonzero(self) -> StageMix:
        if not self.weights:
            raise ValueError("weights must not be empty")
        if sum(self.weights.values()) <= 0:
            raise ValueError("weights must sum to a positive value")
        return self
