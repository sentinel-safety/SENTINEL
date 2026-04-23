# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import Field

from shared.events.topics import Topic
from shared.schemas.base import FrozenModel, UtcDatetime

SCHEMA_VERSION: int = 1


class EventEnvelope[PayloadT](FrozenModel):
    schema_version: int = SCHEMA_VERSION
    id: UUID = Field(default_factory=uuid4)
    topic: Topic
    idempotency_key: str = Field(min_length=1, max_length=200)
    tenant_id: UUID
    published_at: UtcDatetime
    trace_id: str | None = Field(default=None, max_length=64)
    payload: PayloadT
