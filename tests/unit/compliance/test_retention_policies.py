# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import timedelta

import pytest

from compliance.jurisdictions import Jurisdiction
from compliance.retention_policies import (
    RetentionPolicy,
    default_policy,
    strictest_policy,
)

pytestmark = pytest.mark.unit


def test_default_policy_returns_policy_for_jurisdiction() -> None:
    policy = default_policy(Jurisdiction.EU)
    assert policy.jurisdiction == Jurisdiction.EU
    assert policy.events_days == 180


def test_policy_timedelta_properties() -> None:
    policy = default_policy(Jurisdiction.US)
    assert policy.events_timedelta == timedelta(days=policy.events_days)
    assert policy.raw_content_timedelta == timedelta(days=policy.raw_content_days)


def test_strictest_policy_picks_shortest_windows() -> None:
    combined = strictest_policy(frozenset({Jurisdiction.US, Jurisdiction.EU}))
    assert combined.events_days == 180
    assert combined.raw_content_days == 30
    assert combined.audit_log_years == 7


def test_strictest_policy_empty_jurisdictions_raises() -> None:
    with pytest.raises(ValueError, match="at least one jurisdiction"):
        strictest_policy(frozenset())


def test_strictest_policy_single_jurisdiction_matches_default() -> None:
    single = strictest_policy(frozenset({Jurisdiction.UK}))
    default = default_policy(Jurisdiction.UK)
    assert single.events_days == default.events_days
    assert single.audit_log_years == default.audit_log_years


def test_retention_policy_is_frozen() -> None:
    policy = default_policy(Jurisdiction.US)
    with pytest.raises(ValueError, match="Instance is frozen"):
        policy.events_days = 1  # type: ignore[misc]


def test_retention_policy_rejects_unknown_fields() -> None:
    with pytest.raises(ValueError, match="Extra inputs"):
        RetentionPolicy(
            jurisdiction=Jurisdiction.US,
            events_days=30,
            suspicion_profile_days=60,
            audit_log_years=7,
            raw_content_days=7,
            unknown="x",  # type: ignore[call-arg]
        )
