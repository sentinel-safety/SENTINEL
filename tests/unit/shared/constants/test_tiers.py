# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.constants import TIER_RANGES, tier_for_score
from shared.schemas.enums import ResponseTier

pytestmark = pytest.mark.unit


def test_tier_ranges_cover_0_to_100_without_gap_or_overlap() -> None:
    covered: set[int] = set()
    for lo, hi in TIER_RANGES.values():
        for n in range(lo, hi + 1):
            assert n not in covered, f"{n} covered twice"
            covered.add(n)
    assert covered == set(range(0, 101))


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
def test_tier_for_score_matches_spec_5_4(score: int, tier: ResponseTier) -> None:
    assert tier_for_score(score) is tier


@pytest.mark.parametrize("score", [-1, 101, 200])
def test_tier_for_score_rejects_out_of_range(score: int) -> None:
    with pytest.raises(ValueError, match=r"outside 0\.\.100"):
        tier_for_score(score)
