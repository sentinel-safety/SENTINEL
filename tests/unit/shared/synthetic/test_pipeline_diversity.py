# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.synthetic.axes import (
    CommunicationStyle,
    Demographics,
    DiversityAxes,
    GroomingStage,
    Platform,
    StageMix,
)
from shared.synthetic.pipeline import generate_dataset
from tests.unit.shared.synthetic.conftest import make_fake_provider

pytestmark = pytest.mark.unit


async def test_diversity_axes_combinations_covered() -> None:
    d1 = Demographics(age_band="11-13", gender="female", regional_context="US")
    d2 = Demographics(age_band="16-17", gender="male", regional_context="AU")
    axes = DiversityAxes(
        demographics=(d1, d2),
        platforms=(Platform.DM, Platform.GAME_CHAT),
        communication_styles=(CommunicationStyle.CASUAL_TYPING,),
        languages=("en",),
    )
    mix = StageMix(weights={GroomingStage.FRIENDSHIP_FORMING: 1})
    provider = make_fake_provider()
    ds = await generate_dataset(axes=axes, stage_mix=mix, count=40, seed=3, provider=provider)
    combos = {(c.demographics.age_band, c.platform) for c in ds.conversations}
    assert ("11-13", Platform.DM) in combos
    assert ("11-13", Platform.GAME_CHAT) in combos
    assert ("16-17", Platform.DM) in combos
    assert ("16-17", Platform.GAME_CHAT) in combos
