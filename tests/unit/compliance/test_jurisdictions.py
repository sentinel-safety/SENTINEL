# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from compliance.jurisdictions import (
    ComplianceRegime,
    Jurisdiction,
    regimes_for,
    regimes_for_all,
)

pytestmark = pytest.mark.unit


def test_us_regimes_include_coppa_and_ncmec() -> None:
    assert regimes_for(Jurisdiction.US) == frozenset(
        {ComplianceRegime.COPPA, ComplianceRegime.NCMEC}
    )


def test_eu_regimes_include_gdpr_and_dsa() -> None:
    assert regimes_for(Jurisdiction.EU) == frozenset({ComplianceRegime.GDPR, ComplianceRegime.DSA})


def test_uk_regimes_include_uk_osa() -> None:
    assert regimes_for(Jurisdiction.UK) == frozenset({ComplianceRegime.UK_OSA})


def test_regimes_for_all_unions_regime_sets() -> None:
    result = regimes_for_all(frozenset({Jurisdiction.US, Jurisdiction.EU}))
    assert ComplianceRegime.COPPA in result
    assert ComplianceRegime.GDPR in result
    assert ComplianceRegime.DSA in result


def test_regimes_for_all_empty_is_empty() -> None:
    assert regimes_for_all(frozenset()) == frozenset()
