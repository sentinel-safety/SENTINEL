# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.schemas.enums import ResponseTier
from shared.scoring.tier import tier_for_score

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("score", "tier"),
    [
        (0, ResponseTier.TRUSTED),
        (19, ResponseTier.TRUSTED),
        (20, ResponseTier.WATCH),
        (39, ResponseTier.WATCH),
        (40, ResponseTier.ACTIVE_MONITOR),
        (59, ResponseTier.ACTIVE_MONITOR),
        (60, ResponseTier.THROTTLE),
        (74, ResponseTier.THROTTLE),
        (75, ResponseTier.RESTRICT),
        (89, ResponseTier.RESTRICT),
        (90, ResponseTier.CRITICAL),
        (100, ResponseTier.CRITICAL),
    ],
)
def test_tier_boundaries(score: int, tier: ResponseTier) -> None:
    assert tier_for_score(score) is tier


@pytest.mark.parametrize("score", [-1, 101])
def test_tier_rejects_out_of_range(score: int) -> None:
    with pytest.raises(ValueError):
        tier_for_score(score)
