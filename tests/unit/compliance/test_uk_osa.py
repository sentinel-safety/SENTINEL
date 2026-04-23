# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest

from compliance.uk_osa import HarmCategory, RiskAssessment, RiskLevel

pytestmark = pytest.mark.unit

_ASSESS = UUID("11111111-1111-1111-1111-111111111111")
_TENANT = UUID("22222222-2222-2222-2222-222222222222")
_NOW = datetime(2026, 1, 1, tzinfo=UTC)
_DUE = datetime(2026, 7, 1, tzinfo=UTC)


def test_risk_assessment_roundtrips() -> None:
    assess = RiskAssessment(
        assessment_id=_ASSESS,
        tenant_id=_TENANT,
        assessed_at=_NOW,
        harm_category=HarmCategory.GROOMING,
        risk_level=RiskLevel.HIGH,
        mitigations=("realtime_detection", "escalation_tier_3"),
        reviewer="trust_safety_lead",
        next_review_due=_DUE,
    )
    assert assess.harm_category is HarmCategory.GROOMING
    assert assess.risk_level is RiskLevel.HIGH
    assert "realtime_detection" in assess.mitigations


def test_risk_assessment_rejects_empty_reviewer() -> None:
    with pytest.raises(ValueError, match="String should have at least"):
        RiskAssessment(
            assessment_id=_ASSESS,
            tenant_id=_TENANT,
            assessed_at=_NOW,
            harm_category=HarmCategory.BULLYING,
            risk_level=RiskLevel.LOW,
            reviewer="",
            next_review_due=_DUE,
        )
