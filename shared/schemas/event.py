# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from shared.schemas.base import FrozenModel, UtcDatetime
from shared.schemas.enums import EventType


class Event(FrozenModel):
    id: UUID
    tenant_id: UUID
    conversation_id: UUID
    actor_id: UUID
    target_actor_ids: tuple[UUID, ...] = ()
    timestamp: UtcDatetime
    type: EventType
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    content_features: dict[str, Any] = Field(default_factory=dict)
    processed_at: UtcDatetime | None = None
    score_delta: int = 0
    pattern_match_ids: tuple[UUID, ...] = ()
