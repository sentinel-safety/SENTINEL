# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

import orjson
from pydantic import Field

from shared.schemas.base import FrozenModel, UtcDatetime


class WebhookEventKind(StrEnum):
    SCORE_CHANGED = "score.changed"
    TIER_CHANGED = "tier.changed"
    ACTION_RECOMMENDED = "action.recommended"
    PATTERN_MATCHED = "pattern.matched"
    MANDATORY_REPORT_REQUIRED = "mandatory_report.required"


class WebhookEnvelope(FrozenModel):
    delivery_id: UUID
    tenant_id: UUID
    actor_id: UUID
    event_kind: WebhookEventKind
    body: dict[str, Any] = Field(default_factory=dict)
    produced_at: UtcDatetime

    def body_bytes(self) -> bytes:
        payload = {
            "delivery_id": str(self.delivery_id),
            "tenant_id": str(self.tenant_id),
            "actor_id": str(self.actor_id),
            "event_kind": self.event_kind.value,
            "produced_at": self.produced_at.isoformat(),
            "payload": self.body,
        }
        return orjson.dumps(payload, option=orjson.OPT_SORT_KEYS)
