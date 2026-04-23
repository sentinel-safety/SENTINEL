# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from pydantic import Field, model_validator

from shared.schemas.base import FrozenModel, UtcDatetime
from shared.schemas.enums import ChannelType


class Conversation(FrozenModel):
    id: UUID
    tenant_id: UUID
    participant_actor_ids: tuple[UUID, ...] = Field(min_length=1)
    started_at: UtcDatetime
    last_message_at: UtcDatetime
    channel_type: ChannelType

    @model_validator(mode="after")
    def _last_message_after_start(self) -> Conversation:
        if self.last_message_at < self.started_at:
            raise ValueError("last_message_at cannot precede started_at")
        return self

    @model_validator(mode="after")
    def _participants_unique(self) -> Conversation:
        if len(set(self.participant_actor_ids)) != len(self.participant_actor_ids):
            raise ValueError("participant_actor_ids must be unique")
        return self
