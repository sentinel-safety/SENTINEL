from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from shared.schemas.base import FrozenModel, UtcDatetime


class TransparencyReportPeriod(StrEnum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class TransparencyReport(FrozenModel):
    report_id: UUID
    tenant_id: UUID
    period: TransparencyReportPeriod
    period_start: UtcDatetime
    period_end: UtcDatetime
    actions_automated: int = Field(ge=0)
    actions_human_reviewed: int = Field(ge=0)
    actions_reversed_on_appeal: int = Field(ge=0)
    actors_flagged: int = Field(ge=0)
    mandatory_reports_filed: int = Field(ge=0)


class TrustedFlaggerRegistration(FrozenModel):
    registration_id: UUID
    tenant_id: UUID
    flagger_name: str = Field(min_length=1, max_length=200)
    flagger_contact: str = Field(min_length=1, max_length=200)
    registered_at: UtcDatetime
    revoked_at: UtcDatetime | None = None
