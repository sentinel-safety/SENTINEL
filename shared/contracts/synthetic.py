# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from shared.schemas.base import FrozenModel


class GenerateRequest(FrozenModel):
    axes: dict[str, object]
    stage_mix: dict[str, object]
    count: int
    seed: int


class GenerateResponse(FrozenModel):
    run_id: UUID
    status: str
    count: int
