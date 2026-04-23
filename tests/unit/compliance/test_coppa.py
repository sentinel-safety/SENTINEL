# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from compliance.coppa import (
    COPPA_AGE_THRESHOLD,
    COPPA_MAX_RETENTION_DAYS,
    ParentalConsentRecord,
    ParentalConsentStatus,
)

pytestmark = pytest.mark.unit

_TENANT = UUID("11111111-1111-1111-1111-111111111111")
_ACTOR = UUID("22222222-2222-2222-2222-222222222222")
_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


def test_age_threshold_is_thirteen() -> None:
    assert COPPA_AGE_THRESHOLD == 13


def test_max_retention_days_is_ninety() -> None:
    assert COPPA_MAX_RETENTION_DAYS == 90


def test_granted_consent_is_effective_after_grant() -> None:
    record = ParentalConsentRecord(
        tenant_id=_TENANT,
        actor_id=_ACTOR,
        status=ParentalConsentStatus.GRANTED,
        granted_at=_NOW - timedelta(days=1),
        method="verifiable_consent_v1",
    )
    assert record.is_effective_at(_NOW)


def test_granted_consent_not_effective_before_grant() -> None:
    record = ParentalConsentRecord(
        tenant_id=_TENANT,
        actor_id=_ACTOR,
        status=ParentalConsentStatus.GRANTED,
        granted_at=_NOW + timedelta(days=1),
        method="verifiable_consent_v1",
    )
    assert not record.is_effective_at(_NOW)


def test_revoked_consent_not_effective_after_revocation() -> None:
    record = ParentalConsentRecord(
        tenant_id=_TENANT,
        actor_id=_ACTOR,
        status=ParentalConsentStatus.GRANTED,
        granted_at=_NOW - timedelta(days=10),
        revoked_at=_NOW - timedelta(days=1),
        method="verifiable_consent_v1",
    )
    assert not record.is_effective_at(_NOW)


def test_pending_consent_not_effective() -> None:
    record = ParentalConsentRecord(
        tenant_id=_TENANT,
        actor_id=_ACTOR,
        status=ParentalConsentStatus.PENDING,
        method="verifiable_consent_v1",
    )
    assert not record.is_effective_at(_NOW)


def test_granted_without_timestamp_is_not_effective() -> None:
    record = ParentalConsentRecord(
        tenant_id=_TENANT,
        actor_id=_ACTOR,
        status=ParentalConsentStatus.GRANTED,
        method="verifiable_consent_v1",
    )
    assert not record.is_effective_at(_NOW)
