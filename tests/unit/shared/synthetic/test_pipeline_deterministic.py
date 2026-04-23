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


def _axes() -> DiversityAxes:
    return DiversityAxes(
        demographics=(Demographics(age_band="14-15", gender="male", regional_context="UK"),),
        platforms=(Platform.DM,),
        communication_styles=(CommunicationStyle.CASUAL_TYPING,),
        languages=("en",),
    )


def _mix() -> StageMix:
    return StageMix(weights=dict.fromkeys(GroomingStage, 1))


async def test_same_seed_produces_identical_dataset() -> None:
    provider = make_fake_provider()
    ds1 = await generate_dataset(
        axes=_axes(), stage_mix=_mix(), count=6, seed=42, provider=provider
    )
    provider2 = make_fake_provider()
    ds2 = await generate_dataset(
        axes=_axes(), stage_mix=_mix(), count=6, seed=42, provider=provider2
    )
    assert [c.stage for c in ds1.conversations] == [c.stage for c in ds2.conversations]
    assert [c.turns for c in ds1.conversations] == [c.turns for c in ds2.conversations]


async def test_different_seed_produces_different_dataset() -> None:
    provider = make_fake_provider()
    ds1 = await generate_dataset(
        axes=_axes(), stage_mix=_mix(), count=12, seed=1, provider=provider
    )
    provider2 = make_fake_provider()
    ds2 = await generate_dataset(
        axes=_axes(), stage_mix=_mix(), count=12, seed=2, provider=provider2
    )
    stages1 = [c.stage for c in ds1.conversations]
    stages2 = [c.stage for c in ds2.conversations]
    assert stages1 != stages2


async def test_dataset_count_matches_request() -> None:
    provider = make_fake_provider()
    ds = await generate_dataset(
        axes=_axes(), stage_mix=_mix(), count=10, seed=99, provider=provider
    )
    assert len(ds.conversations) == 10
