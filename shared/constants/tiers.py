# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


"""Tier boundaries from SENTINEL_SPECIFICATION section 5.4."""

from __future__ import annotations

from typing import Final

from shared.schemas.enums import ResponseTier

TIER_RANGES: Final[dict[ResponseTier, tuple[int, int]]] = {
    ResponseTier.TRUSTED: (0, 19),
    ResponseTier.WATCH: (20, 39),
    ResponseTier.ACTIVE_MONITOR: (40, 59),
    ResponseTier.THROTTLE: (60, 74),
    ResponseTier.RESTRICT: (75, 89),
    ResponseTier.CRITICAL: (90, 100),
}

TIER_NAMES: Final[dict[ResponseTier, str]] = {
    ResponseTier.TRUSTED: "Trusted",
    ResponseTier.WATCH: "Watch",
    ResponseTier.ACTIVE_MONITOR: "Active Monitor",
    ResponseTier.THROTTLE: "Throttle",
    ResponseTier.RESTRICT: "Restrict",
    ResponseTier.CRITICAL: "Critical",
}


def tier_for_score(score: int) -> ResponseTier:
    if not 0 <= score <= 100:
        raise ValueError(f"score {score} outside 0..100")
    for tier, (lo, hi) in TIER_RANGES.items():
        if lo <= score <= hi:
            return tier
    raise AssertionError("unreachable: tier ranges cover 0..100")  # pragma: no cover
