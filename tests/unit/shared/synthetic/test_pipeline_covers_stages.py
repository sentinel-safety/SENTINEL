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


async def test_all_six_stages_covered() -> None:
    axes = DiversityAxes(
        demographics=(Demographics(age_band="14-15", gender="male", regional_context="UK"),),
        platforms=(Platform.DM,),
        communication_styles=(CommunicationStyle.CASUAL_TYPING,),
        languages=("en",),
    )
    mix = StageMix(weights=dict.fromkeys(GroomingStage, 1))
    provider = make_fake_provider()
    ds = await generate_dataset(axes=axes, stage_mix=mix, count=60, seed=7, provider=provider)
    stages_present = {c.stage for c in ds.conversations}
    assert stages_present == set(GroomingStage)
