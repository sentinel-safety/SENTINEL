# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from pydantic import Field

from shared.memory import ActorMemoryView
from shared.schemas.base import FrozenModel


class MemoryLookupRequest(FrozenModel):
    tenant_id: UUID
    actor_id: UUID
    lookback_days: int = Field(default=21, ge=1, le=365)


class MemoryLookupResponse(FrozenModel):
    view: ActorMemoryView
