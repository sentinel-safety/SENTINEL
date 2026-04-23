# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from pydantic import Field, model_validator

from shared.schemas.base import FrozenModel, UtcDatetime
from shared.schemas.enums import ResponseTier
from shared.schemas.reasoning import Reasoning


class TierChangeEvent(FrozenModel):
    tenant_id: UUID
    actor_id: UUID
    event_id: UUID
    previous_tier: ResponseTier
    new_tier: ResponseTier
    new_score: int = Field(ge=0, le=100)
    triggered_at: UtcDatetime
    reasoning: Reasoning | None = None

    @model_validator(mode="after")
    def _tiers_must_differ(self) -> TierChangeEvent:
        if self.previous_tier == self.new_tier:
            raise ValueError("TierChangeEvent previous_tier and new_tier must differ")
        return self
