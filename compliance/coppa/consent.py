from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from shared.schemas.base import FrozenModel, UtcDatetime


class ParentalConsentStatus(StrEnum):
    UNKNOWN = "unknown"
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    GRANTED = "granted"
    REVOKED = "revoked"


class ParentalConsentRecord(FrozenModel):
    tenant_id: UUID
    actor_id: UUID
    status: ParentalConsentStatus
    granted_at: UtcDatetime | None = None
    revoked_at: UtcDatetime | None = None
    method: str = Field(min_length=1, max_length=50)
    evidence_reference: str | None = Field(default=None, max_length=255)

    def is_effective_at(self, when: datetime) -> bool:
        if self.status != ParentalConsentStatus.GRANTED:
            return False
        if self.granted_at is None or self.granted_at > when:
            return False
        return not (self.revoked_at is not None and self.revoked_at <= when)


COPPA_AGE_THRESHOLD: int = 13
COPPA_MAX_RETENTION_DAYS: int = 90
