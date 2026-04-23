# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from pydantic import Field, field_serializer, field_validator

from shared.schemas.base import FrozenModel, UtcDatetime
from shared.schemas.enums import ResponseTier


class PrimaryDriver(FrozenModel):
    pattern: str = Field(min_length=1, max_length=100)
    pattern_id: str = Field(min_length=1, max_length=100)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str = Field(min_length=1, max_length=2000)


class Reasoning(FrozenModel):
    actor_id: UUID
    tenant_id: UUID
    score_change: int
    new_score: int = Field(ge=0, le=100)
    new_tier: ResponseTier
    primary_drivers: tuple[PrimaryDriver, ...] = ()
    context: str = Field(default="", max_length=2000)
    recommended_action_summary: str = Field(default="", max_length=500)
    generated_at: UtcDatetime
    next_review_at: UtcDatetime | None = None

    @field_validator("new_tier", mode="before")
    @classmethod
    def _parse_new_tier(cls, value: object) -> ResponseTier:
        if isinstance(value, ResponseTier):
            return value
        if isinstance(value, str):
            return ResponseTier[value.upper()]
        if isinstance(value, int):
            return ResponseTier(value)
        return ResponseTier(int(str(value)))

    @field_serializer("new_tier")
    def _serialize_new_tier(self, value: ResponseTier) -> str:
        return value.name.lower()
