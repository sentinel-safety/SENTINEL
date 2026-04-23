# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import datetime, timedelta

from shared.schemas.enums import ResponseTier


def compute_next_review_at(tier: ResponseTier, *, now: datetime) -> datetime | None:
    if tier >= ResponseTier.THROTTLE:
        return now + timedelta(hours=24)
    if tier == ResponseTier.ACTIVE_MONITOR:
        return now + timedelta(hours=72)
    return None
