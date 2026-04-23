# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field

from shared.schemas.base import FrozenModel, UtcDatetime
from shared.schemas.enums import ResponseTier
from shared.schemas.reasoning import Reasoning


class ActionKind(StrEnum):
    NONE = "none"
    SILENT_LOG = "silent_log"
    REVIEW_QUEUE = "review_queue"
    THROTTLE_DM_TO_MINORS = "throttle_dm_to_minors"
    DISABLE_MEDIA_TO_MINORS = "disable_media_to_minors"
    REQUIRE_APPROVAL_TO_FRIEND_MINOR = "require_approval_to_friend_minor"
    RESTRICT_TO_PUBLIC_POSTS = "restrict_to_public_posts"
    BLOCK_DM_TO_MINORS = "block_dm_to_minors"
    ACCOUNT_WARNING = "account_warning"
    SUSPEND = "suspend"
    MANDATORY_REPORT = "mandatory_report"


class RecommendedAction(FrozenModel):
    kind: ActionKind
    description: str = Field(min_length=1, max_length=500)
    parameters: dict[str, Any] = Field(default_factory=dict)


class ResponseAction(FrozenModel):
    id: UUID
    tenant_id: UUID
    actor_id: UUID
    tier: ResponseTier
    actions: tuple[RecommendedAction, ...] = ()
    triggered_at: UtcDatetime
    triggered_by_event_id: UUID | None = None
    reasoning: Reasoning
    delivered_to_platform_at: UtcDatetime | None = None
    acknowledged_by_platform_at: UtcDatetime | None = None
