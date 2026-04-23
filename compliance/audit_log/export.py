from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from shared.schemas.base import FrozenModel, UtcDatetime


class AuditExportFormat(StrEnum):
    JSONL = "jsonl"
    CSV = "csv"


class AuditExportRequest(FrozenModel):
    request_id: UUID
    tenant_id: UUID
    requested_by: str = Field(min_length=1, max_length=200)
    requested_at: UtcDatetime
    format: AuditExportFormat
    period_start: UtcDatetime
    period_end: UtcDatetime


AUDIT_LOG_RETENTION_YEARS: int = 7
