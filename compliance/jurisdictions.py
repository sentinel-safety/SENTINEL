from __future__ import annotations

from enum import StrEnum


class Jurisdiction(StrEnum):
    US = "US"
    EU = "EU"
    UK = "UK"


class ComplianceRegime(StrEnum):
    COPPA = "COPPA"
    GDPR = "GDPR"
    DSA = "DSA"
    UK_OSA = "UK_OSA"
    NCMEC = "NCMEC"


_REGIMES_BY_JURISDICTION: dict[Jurisdiction, frozenset[ComplianceRegime]] = {
    Jurisdiction.US: frozenset({ComplianceRegime.COPPA, ComplianceRegime.NCMEC}),
    Jurisdiction.EU: frozenset({ComplianceRegime.GDPR, ComplianceRegime.DSA}),
    Jurisdiction.UK: frozenset({ComplianceRegime.UK_OSA}),
}


def regimes_for(jurisdiction: Jurisdiction) -> frozenset[ComplianceRegime]:
    return _REGIMES_BY_JURISDICTION[jurisdiction]


def regimes_for_all(jurisdictions: frozenset[Jurisdiction]) -> frozenset[ComplianceRegime]:
    return frozenset().union(*(regimes_for(j) for j in jurisdictions))
