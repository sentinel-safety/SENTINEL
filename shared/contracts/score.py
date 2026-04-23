# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from pydantic import Field, field_serializer, field_validator

from shared.schemas.base import FrozenModel
from shared.schemas.enums import ResponseTier
from shared.schemas.event import Event
from shared.schemas.reasoning import Reasoning
from shared.scoring.signals import ScoreSignal


class ScoreRequest(FrozenModel):
    event: Event
    signals: tuple[ScoreSignal, ...] = ()


class ScoreResponse(FrozenModel):
    current_score: int = Field(ge=0, le=100)
    previous_score: int = Field(ge=0, le=100)
    delta: int
    tier: ResponseTier
    reasoning: Reasoning | None = None

    @field_validator("tier", mode="before")
    @classmethod
    def parse_tier(cls, value: object) -> ResponseTier:
        if isinstance(value, str):
            return ResponseTier[value.upper()]
        if isinstance(value, int):
            return ResponseTier(value)
        return ResponseTier(int(str(value)))

    @field_serializer("tier")
    def serialize_tier(self, value: ResponseTier) -> str:
        return value.name.lower()
