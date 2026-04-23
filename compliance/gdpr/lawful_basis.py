from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from shared.schemas.base import FrozenModel, UtcDatetime


class LawfulBasis(StrEnum):
    CONSENT = "consent"
    CONTRACT = "contract"
    LEGAL_OBLIGATION = "legal_obligation"
    VITAL_INTERESTS = "vital_interests"
    PUBLIC_TASK = "public_task"
    LEGITIMATE_INTERESTS = "legitimate_interests"


class LawfulBasisDeclaration(FrozenModel):
    tenant_id: UUID
    basis: LawfulBasis
    documented_at: UtcDatetime
    documentation_uri: str = Field(min_length=1, max_length=500)
    notes: str | None = Field(default=None, max_length=2000)
