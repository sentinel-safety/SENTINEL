from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from shared.schemas.base import FrozenModel, UtcDatetime


class HarmCategory(StrEnum):
    CSEA = "child_sexual_exploitation_abuse"
    GROOMING = "grooming"
    BULLYING = "bullying"
    SELF_HARM = "self_harm"
    HATE = "hate"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskAssessment(FrozenModel):
    assessment_id: UUID
    tenant_id: UUID
    assessed_at: UtcDatetime
    harm_category: HarmCategory
    risk_level: RiskLevel
    mitigations: tuple[str, ...] = Field(default_factory=tuple)
    reviewer: str = Field(min_length=1, max_length=200)
    next_review_due: UtcDatetime
