# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from hashlib import sha256
from typing import Any, Final
from uuid import UUID

import orjson
from pydantic import Field

from shared.schemas.base import FrozenModel, UtcDatetime

HASH_HEX_LEN: Final[int] = 64
GENESIS_HASH: Final[str] = "0" * HASH_HEX_LEN


class AuditEntryPayload(FrozenModel):
    tenant_id: UUID
    sequence: int = Field(ge=1)
    actor_id: UUID | None
    event_type: str = Field(min_length=1, max_length=100)
    details: dict[str, Any]
    timestamp: UtcDatetime
    previous_entry_hash: str = Field(min_length=HASH_HEX_LEN, max_length=HASH_HEX_LEN)


def compute_entry_hash(payload: AuditEntryPayload) -> str:
    material = orjson.dumps(
        {
            "tenant_id": str(payload.tenant_id),
            "sequence": payload.sequence,
            "actor_id": str(payload.actor_id) if payload.actor_id is not None else None,
            "event_type": payload.event_type,
            "details": payload.details,
            "timestamp": payload.timestamp.isoformat(),
            "previous_entry_hash": payload.previous_entry_hash,
        },
        option=orjson.OPT_SORT_KEYS,
    )
    return sha256(material).hexdigest()
