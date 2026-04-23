# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.constants import (
    GROOMING_DESENSITIZATION_DELTA,
    GROOMING_EXCLUSIVITY_DELTA,
    GROOMING_FRIENDSHIP_FORMING_DELTA,
    GROOMING_ISOLATION_DELTA,
    GROOMING_RISK_ASSESSMENT_DELTA,
    GROOMING_SEXUAL_ESCALATION_DELTA,
    MAX_SCORE,
    MIN_SCORE,
    MINIMUM_SCORE_FLOOR,
    NEW_ACCOUNT_BASELINE_SCORE,
    PERSONAL_INFO_REQUEST_DELTA,
    PHOTO_REQUEST_DELTA,
    PLATFORM_MIGRATION_REQUEST_DELTA,
    SECRECY_REQUEST_DELTA,
    VIDEO_REQUEST_DELTA,
    clamp_score,
)

pytestmark = pytest.mark.unit


def test_score_bounds_match_spec() -> None:
    assert MIN_SCORE == 0
    assert MAX_SCORE == 100
    assert NEW_ACCOUNT_BASELINE_SCORE == 5
    assert MINIMUM_SCORE_FLOOR == 5


def test_grooming_stage_deltas_match_spec_5_2() -> None:
    assert GROOMING_FRIENDSHIP_FORMING_DELTA == 2
    assert GROOMING_RISK_ASSESSMENT_DELTA == 6
    assert GROOMING_EXCLUSIVITY_DELTA == 5
    assert GROOMING_ISOLATION_DELTA == 12
    assert GROOMING_DESENSITIZATION_DELTA == 15
    assert GROOMING_SEXUAL_ESCALATION_DELTA == 25


def test_behavioral_marker_deltas_match_spec_5_2() -> None:
    assert PERSONAL_INFO_REQUEST_DELTA == 8
    assert PHOTO_REQUEST_DELTA == 15
    assert VIDEO_REQUEST_DELTA == 20
    assert PLATFORM_MIGRATION_REQUEST_DELTA == 18
    assert SECRECY_REQUEST_DELTA == 20


@pytest.mark.parametrize(
    ("raw", "clamped"),
    [
        (-5, 0),
        (0, 0),
        (50, 50),
        (100, 100),
        (150, 100),
    ],
)
def test_clamp_score(raw: int, clamped: int) -> None:
    assert clamp_score(raw) == clamped
