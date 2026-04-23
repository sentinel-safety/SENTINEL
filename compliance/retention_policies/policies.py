from __future__ import annotations

from datetime import timedelta

from compliance.jurisdictions import Jurisdiction
from shared.schemas.base import FrozenModel


class RetentionPolicy(FrozenModel):
    jurisdiction: Jurisdiction
    events_days: int
    suspicion_profile_days: int
    audit_log_years: int
    raw_content_days: int

    @property
    def events_timedelta(self) -> timedelta:
        return timedelta(days=self.events_days)

    @property
    def raw_content_timedelta(self) -> timedelta:
        return timedelta(days=self.raw_content_days)


_POLICIES: dict[Jurisdiction, RetentionPolicy] = {
    Jurisdiction.US: RetentionPolicy(
        jurisdiction=Jurisdiction.US,
        events_days=365,
        suspicion_profile_days=730,
        audit_log_years=7,
        raw_content_days=90,
    ),
    Jurisdiction.EU: RetentionPolicy(
        jurisdiction=Jurisdiction.EU,
        events_days=180,
        suspicion_profile_days=365,
        audit_log_years=7,
        raw_content_days=30,
    ),
    Jurisdiction.UK: RetentionPolicy(
        jurisdiction=Jurisdiction.UK,
        events_days=365,
        suspicion_profile_days=730,
        audit_log_years=7,
        raw_content_days=90,
    ),
}


def default_policy(jurisdiction: Jurisdiction) -> RetentionPolicy:
    return _POLICIES[jurisdiction]


def strictest_policy(jurisdictions: frozenset[Jurisdiction]) -> RetentionPolicy:
    if not jurisdictions:
        raise ValueError("at least one jurisdiction required")
    policies = [_POLICIES[j] for j in jurisdictions]
    primary = min(jurisdictions, key=lambda j: _POLICIES[j].events_days)
    return RetentionPolicy(
        jurisdiction=primary,
        events_days=min(p.events_days for p in policies),
        suspicion_profile_days=min(p.suspicion_profile_days for p in policies),
        audit_log_years=max(p.audit_log_years for p in policies),
        raw_content_days=min(p.raw_content_days for p in policies),
    )
