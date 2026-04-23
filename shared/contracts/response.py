# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from pydantic import Field

from shared.response.tier_change import TierChangeEvent
from shared.schemas.base import FrozenModel, UtcDatetime


class EvaluateResponseRequest(FrozenModel):
    tier_change: TierChangeEvent


class EvaluateResponseResponse(FrozenModel):
    enqueued: bool
    recommended_action_kinds: tuple[str, ...] = ()


class DeadLetterEntry(FrozenModel):
    entry_id: str = Field(min_length=1)
    tenant_id: UUID
    actor_id: UUID
    event_kind: str
    attempt: int = Field(ge=1)
    reason: str
    enqueued_at: UtcDatetime


class DeadLetterListResponse(FrozenModel):
    entries: tuple[DeadLetterEntry, ...] = ()
