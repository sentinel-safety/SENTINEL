# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from pydantic import Field

from shared.schemas.base import FrozenModel, UtcDatetime
from shared.schemas.enums import GroomingStage


class PatternMatch(FrozenModel):
    id: UUID
    tenant_id: UUID
    actor_id: UUID
    pattern_id: str = Field(min_length=1, max_length=100)
    pattern_version: str = Field(min_length=1, max_length=20)
    confidence: float = Field(ge=0.0, le=1.0)
    event_ids: tuple[UUID, ...] = Field(min_length=1)
    matched_at: UtcDatetime
    evidence_summary: str = Field(min_length=1, max_length=2000)
    stage: GroomingStage | None = None
