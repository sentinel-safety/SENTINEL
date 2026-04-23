# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest
from pydantic import ValidationError

from shared.synthetic.axes import (
    CommunicationStyle,
    Demographics,
    DiversityAxes,
    GroomingStage,
    Platform,
    StageMix,
)

pytestmark = pytest.mark.unit


def _default_axes() -> DiversityAxes:
    return DiversityAxes(
        demographics=(Demographics(age_band="14-15", gender="male", regional_context="UK"),),
        platforms=(Platform.DM,),
        communication_styles=(CommunicationStyle.CASUAL_TYPING,),
        languages=("en",),
    )


def test_grooming_stage_has_six_values() -> None:
    assert len(list(GroomingStage)) == 6


def test_grooming_stage_values() -> None:
    assert GroomingStage.FRIENDSHIP_FORMING.value == "friendship_forming"
    assert GroomingStage.SEXUAL_ESCALATION.value == "sexual_escalation"


def test_demographics_valid() -> None:
    d = Demographics(age_band="11-13", gender="female", regional_context="US")
    assert d.age_band == "11-13"


def test_demographics_invalid_age_band() -> None:
    with pytest.raises(ValidationError):
        Demographics(age_band="18-25", gender="female", regional_context="US")


def test_platform_values() -> None:
    assert Platform.DM.value == "dm"
    assert Platform.GAME_CHAT.value == "game_chat"


def test_communication_style_values() -> None:
    assert CommunicationStyle.EMOJI_HEAVY.value == "emoji_heavy"


def test_diversity_axes_valid() -> None:
    axes = _default_axes()
    assert len(axes.demographics) == 1
    assert axes.languages == ("en",)


def test_diversity_axes_empty_demographics_rejected() -> None:
    with pytest.raises(ValidationError):
        DiversityAxes(
            demographics=(),
            platforms=(Platform.DM,),
            communication_styles=(CommunicationStyle.CASUAL_TYPING,),
            languages=("en",),
        )


def test_diversity_axes_empty_platforms_rejected() -> None:
    with pytest.raises(ValidationError):
        DiversityAxes(
            demographics=(Demographics(age_band="14-15", gender="male", regional_context="UK"),),
            platforms=(),
            communication_styles=(CommunicationStyle.CASUAL_TYPING,),
            languages=("en",),
        )


def test_diversity_axes_empty_languages_rejected() -> None:
    with pytest.raises(ValidationError):
        DiversityAxes(
            demographics=(Demographics(age_band="14-15", gender="male", regional_context="UK"),),
            platforms=(Platform.DM,),
            communication_styles=(CommunicationStyle.CASUAL_TYPING,),
            languages=(),
        )


def test_stage_mix_valid() -> None:
    mix = StageMix(weights={GroomingStage.FRIENDSHIP_FORMING: 3, GroomingStage.ISOLATION: 1})
    assert mix.weights[GroomingStage.FRIENDSHIP_FORMING] == 3


def test_stage_mix_zero_sum_rejected() -> None:
    with pytest.raises(ValidationError):
        StageMix(weights={GroomingStage.FRIENDSHIP_FORMING: 0})


def test_stage_mix_empty_rejected() -> None:
    with pytest.raises(ValidationError):
        StageMix(weights={})
