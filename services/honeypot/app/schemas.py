# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from shared.schemas.base import FrozenModel


class EvaluateRequest(FrozenModel):
    tenant_id: UUID
    actor_id: UUID
    actor_tier: int = Field(ge=0, le=5)
    persona_id: str = Field(min_length=1, max_length=64)
    conversation_excerpt: tuple[str, ...] = Field(default=(), max_length=20)
    pattern_matches: tuple[dict[str, Any], ...] = Field(default=())
    reasoning_snapshot: dict[str, Any] = Field(default_factory=dict)


class EvaluateResponseAllowed(FrozenModel):
    decision: str = "allow"
    reply: str
    persona_id: str
    prompt_version: str
    synthetic_header: str = "X-Sentinel-Honeypot: synthetic"


class EvaluateResponseDenied(FrozenModel):
    decision: str = "deny"
    reasons: tuple[str, ...]


class EvidenceResponse(FrozenModel):
    id: UUID
    tenant_id: UUID
    actor_id: UUID
    persona_id: str
    content_hash: str
    created_at: datetime
    synthetic_persona: bool = True
    json_payload: dict[str, Any]
