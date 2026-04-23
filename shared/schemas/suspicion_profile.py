# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from shared.schemas.base import FrozenModel, UtcDatetime
from shared.schemas.enums import ResponseTier


class ScoreHistoryEntry(FrozenModel):
    at: UtcDatetime
    delta: int
    cause: str = Field(min_length=1, max_length=200)
    new_score: int = Field(ge=0, le=100)
    source_event_id: UUID | None = None
    pattern_match_id: UUID | None = None


class ModeratorNote(FrozenModel):
    at: UtcDatetime
    author_id: UUID
    body: str = Field(min_length=1, max_length=5000)


class SuspicionProfile(FrozenModel):
    actor_id: UUID
    tenant_id: UUID
    current_score: int = Field(ge=0, le=100)
    tier: ResponseTier
    tier_entered_at: UtcDatetime
    last_updated: UtcDatetime
    last_decay_applied: UtcDatetime | None = None
    score_history: tuple[ScoreHistoryEntry, ...] = ()
    pattern_matches: tuple[UUID, ...] = ()
    escalation_markers: tuple[str, ...] = ()
    network_signals: dict[str, Any] = Field(default_factory=dict)
    notes: tuple[ModeratorNote, ...] = ()
