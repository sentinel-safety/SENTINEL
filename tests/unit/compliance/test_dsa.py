# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from compliance.dsa import (
    TransparencyReport,
    TransparencyReportPeriod,
    TrustedFlaggerRegistration,
)

pytestmark = pytest.mark.unit

_TENANT = UUID("11111111-1111-1111-1111-111111111111")
_REPORT = UUID("22222222-2222-2222-2222-222222222222")
_REG = UUID("33333333-3333-3333-3333-333333333333")
_START = datetime(2026, 1, 1, tzinfo=UTC)
_END = datetime(2026, 2, 1, tzinfo=UTC)


def test_transparency_report_requires_nonnegative_counts() -> None:
    report = TransparencyReport(
        report_id=_REPORT,
        tenant_id=_TENANT,
        period=TransparencyReportPeriod.MONTHLY,
        period_start=_START,
        period_end=_END,
        actions_automated=0,
        actions_human_reviewed=0,
        actions_reversed_on_appeal=0,
        actors_flagged=0,
        mandatory_reports_filed=0,
    )
    assert report.period is TransparencyReportPeriod.MONTHLY


def test_transparency_report_rejects_negative_counts() -> None:
    with pytest.raises(ValueError, match="greater than or equal to 0"):
        TransparencyReport(
            report_id=_REPORT,
            tenant_id=_TENANT,
            period=TransparencyReportPeriod.MONTHLY,
            period_start=_START,
            period_end=_END,
            actions_automated=-1,
            actions_human_reviewed=0,
            actions_reversed_on_appeal=0,
            actors_flagged=0,
            mandatory_reports_filed=0,
        )


def test_trusted_flagger_registration_roundtrips() -> None:
    reg = TrustedFlaggerRegistration(
        registration_id=_REG,
        tenant_id=_TENANT,
        flagger_name="Example NGO",
        flagger_contact="ops@example.org",
        registered_at=_START,
    )
    assert reg.revoked_at is None
