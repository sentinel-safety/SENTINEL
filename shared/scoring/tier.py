# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from shared.schemas.enums import ResponseTier

_BANDS: tuple[tuple[int, ResponseTier], ...] = (
    (19, ResponseTier.TRUSTED),
    (39, ResponseTier.WATCH),
    (59, ResponseTier.ACTIVE_MONITOR),
    (74, ResponseTier.THROTTLE),
    (89, ResponseTier.RESTRICT),
    (100, ResponseTier.CRITICAL),
)


def tier_for_score(score: int) -> ResponseTier:
    if score < 0 or score > 100:
        raise ValueError(f"score out of range: {score}")
    for ceiling, tier in _BANDS:
        if score <= ceiling:
            return tier
    raise AssertionError("unreachable")
