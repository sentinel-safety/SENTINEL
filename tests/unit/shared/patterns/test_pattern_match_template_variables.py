# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest
from pydantic import ValidationError

from shared.patterns.matches import DetectionMode, PatternMatch
from shared.scoring.signals import SignalKind

pytestmark = pytest.mark.unit


def test_template_variables_default_empty() -> None:
    match = PatternMatch(
        pattern_name="late_night",
        signal_kind=SignalKind.LATE_NIGHT_MINOR_CONTACT,
        confidence=1.0,
        evidence_excerpts=("late-night",),
        detection_mode=DetectionMode.RULE,
        prompt_version=None,
    )
    assert match.template_variables == {}


def test_template_variables_accepts_scalars() -> None:
    match = PatternMatch(
        pattern_name="multi_minor_contact",
        signal_kind=SignalKind.MULTI_MINOR_CONTACT_WINDOW,
        confidence=0.7,
        evidence_excerpts=("3 minors",),
        detection_mode=DetectionMode.RULE,
        prompt_version=None,
        template_variables={
            "distinct_minors": 3,
            "lookback_days": 7,
            "velocity_per_day": 0.42,
        },
    )
    assert match.template_variables["distinct_minors"] == 3
    assert match.template_variables["lookback_days"] == 7
    assert match.template_variables["velocity_per_day"] == pytest.approx(0.42)


def test_pattern_match_is_still_frozen() -> None:
    match = PatternMatch(
        pattern_name="late_night",
        signal_kind=SignalKind.LATE_NIGHT_MINOR_CONTACT,
        confidence=1.0,
        evidence_excerpts=("x",),
        detection_mode=DetectionMode.RULE,
        prompt_version=None,
    )
    with pytest.raises(ValidationError):
        match.template_variables = {"x": 1}  # type: ignore[misc]
