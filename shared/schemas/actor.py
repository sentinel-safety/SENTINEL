# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from shared.schemas.base import FrozenModel, UtcDatetime
from shared.schemas.enums import AgeBand


class Actor(FrozenModel):
    id: UUID
    tenant_id: UUID
    external_id_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    claimed_age_band: AgeBand = AgeBand.UNKNOWN
    account_created_at: UtcDatetime
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def is_minor(self) -> bool:
        return self.claimed_age_band in {AgeBand.UNDER_13, AgeBand.BAND_13_15, AgeBand.BAND_16_17}
