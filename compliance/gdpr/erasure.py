from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from shared.schemas.base import FrozenModel, UtcDatetime


class ErasureRequestStatus(StrEnum):
    RECEIVED = "received"
    VERIFIED = "verified"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class ErasureRequest(FrozenModel):
    request_id: UUID
    tenant_id: UUID
    actor_id: UUID
    received_at: UtcDatetime
    status: ErasureRequestStatus
    justification: str | None = Field(default=None, max_length=2000)
    completed_at: UtcDatetime | None = None

    def is_terminal(self) -> bool:
        return self.status in {ErasureRequestStatus.COMPLETED, ErasureRequestStatus.REJECTED}
