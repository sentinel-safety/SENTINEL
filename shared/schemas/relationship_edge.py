# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from shared.schemas.base import FrozenModel, UtcDatetime


class RelationshipEdge(FrozenModel):
    tenant_id: UUID
    actor_a: UUID
    actor_b: UUID
    interaction_count: int = Field(ge=0)
    first_interaction: UtcDatetime
    last_interaction: UtcDatetime
    signals: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _ordered_and_distinct(self) -> RelationshipEdge:
        if self.actor_a == self.actor_b:
            raise ValueError("RelationshipEdge cannot self-loop")
        if bytes(self.actor_a.bytes) > bytes(self.actor_b.bytes):
            raise ValueError("actor_a must be the lexicographically smaller UUID")
        if self.last_interaction < self.first_interaction:
            raise ValueError("last_interaction cannot precede first_interaction")
        return self
