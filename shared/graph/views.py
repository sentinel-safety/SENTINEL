# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from pydantic import Field

from shared.schemas.base import FrozenModel


class ContactGraphView(FrozenModel):
    distinct_contacts_total: int = Field(ge=0)
    distinct_minor_contacts_window: int = Field(ge=0)
    contact_velocity_per_day: float = Field(ge=0.0)
    age_band_distribution: dict[str, int]
    lookback_days: int = Field(ge=1, le=90)
