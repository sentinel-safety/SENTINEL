# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field, field_serializer, field_validator

from shared.schemas.base import FrozenModel, UtcDatetime
from shared.schemas.enums import EventType, ResponseTier
from shared.scoring.signals import ScoreSignal


class IngestEventRequest(FrozenModel):
    idempotency_key: str = Field(min_length=1, max_length=200)
    tenant_id: UUID
    conversation_id: UUID
    actor_external_id_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    target_actor_external_id_hashes: tuple[str, ...] = ()
    event_type: EventType
    timestamp: UtcDatetime
    content: str = Field(default="", max_length=20_000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IngestEventResponse(FrozenModel):
    event_id: UUID
    current_score: int = Field(ge=0, le=100)
    tier: ResponseTier
    delta: int
    signals: tuple[ScoreSignal, ...] = ()

    @field_validator("tier", mode="before")
    @classmethod
    def parse_tier(cls, value: object) -> ResponseTier:
        if isinstance(value, str):
            return ResponseTier[value.upper()]
        if isinstance(value, int):
            return ResponseTier(value)
        return ResponseTier(int(str(value)))

    @field_serializer("tier")
    def serialize_tier(self, value: ResponseTier) -> str:
        return value.name.lower()


class ActorStateResponse(FrozenModel):
    actor_id: UUID
    tenant_id: UUID
    current_score: int = Field(ge=0, le=100)
    tier: ResponseTier
    last_updated: UtcDatetime

    @field_validator("tier", mode="before")
    @classmethod
    def parse_tier(cls, value: object) -> ResponseTier:
        if isinstance(value, str):
            return ResponseTier[value.upper()]
        if isinstance(value, int):
            return ResponseTier(value)
        return ResponseTier(int(str(value)))

    @field_serializer("tier")
    def serialize_tier(self, value: ResponseTier) -> str:
        return value.name.lower()
