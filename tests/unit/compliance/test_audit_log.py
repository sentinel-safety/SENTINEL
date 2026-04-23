# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from compliance.audit_log import (
    AUDIT_LOG_RETENTION_YEARS,
    AuditExportFormat,
    AuditExportRequest,
)

pytestmark = pytest.mark.unit

_REQ = UUID("11111111-1111-1111-1111-111111111111")
_TENANT = UUID("22222222-2222-2222-2222-222222222222")
_START = datetime(2026, 1, 1, tzinfo=UTC)
_END = datetime(2026, 2, 1, tzinfo=UTC)


def test_retention_is_seven_years() -> None:
    assert AUDIT_LOG_RETENTION_YEARS == 7


def test_export_request_roundtrips() -> None:
    req = AuditExportRequest(
        request_id=_REQ,
        tenant_id=_TENANT,
        requested_by="auditor@example.com",
        requested_at=_START,
        format=AuditExportFormat.JSONL,
        period_start=_START,
        period_end=_END,
    )
    assert req.format is AuditExportFormat.JSONL


def test_export_format_has_csv_variant() -> None:
    assert AuditExportFormat.CSV.value == "csv"
