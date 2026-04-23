from __future__ import annotations

from datetime import datetime
from enum import IntEnum, StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


class EventType(StrEnum):
    MESSAGE = "message"
    IMAGE = "image"
    FRIEND_REQUEST = "friend_request"
    GIFT = "gift"
    PROFILE_CHANGE = "profile_change"
    VOICE_CLIP = "voice_clip"


class ResponseTier(IntEnum):
    TRUSTED = 0
    WATCH = 1
    ACTIVE_MONITOR = 2
    THROTTLE = 3
    RESTRICT = 4
    CRITICAL = 5


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


class _Model(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True, str_strip_whitespace=True)


def _parse_tier(value: object) -> ResponseTier:
    if isinstance(value, ResponseTier):
        return value
    if isinstance(value, str):
        return ResponseTier[value.upper()]
    if isinstance(value, int):
        return ResponseTier(value)
    return ResponseTier(int(str(value)))


class PrimaryDriver(_Model):
    pattern: str = Field(min_length=1, max_length=100)
    pattern_id: str = Field(min_length=1, max_length=100)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str = Field(min_length=1, max_length=2000)


class RecommendedAction(_Model):
    kind: ActionKind
    description: str = Field(min_length=1, max_length=500)
    parameters: dict[str, Any] = Field(default_factory=dict)


class Reasoning(_Model):
    actor_id: UUID
    tenant_id: UUID
    score_change: int
    new_score: int = Field(ge=0, le=100)
    new_tier: ResponseTier
    primary_drivers: tuple[PrimaryDriver, ...] = ()
    context: str = Field(default="", max_length=2000)
    recommended_action_summary: str = Field(default="", max_length=500)
    generated_at: datetime
    next_review_at: datetime | None = None

    @field_validator("new_tier", mode="before")
    @classmethod
    def _parse_new_tier(cls, value: object) -> ResponseTier:
        return _parse_tier(value)

    @field_serializer("new_tier")
    def _serialize_new_tier(self, value: ResponseTier) -> str:
        return value.name.lower()


class ScoreResult(_Model):
    current_score: int = Field(ge=0, le=100)
    previous_score: int = Field(ge=0, le=100)
    delta: int
    tier: ResponseTier
    reasoning: Reasoning | None = None

    @field_validator("tier", mode="before")
    @classmethod
    def _parse_tier_field(cls, value: object) -> ResponseTier:
        return _parse_tier(value)

    @field_serializer("tier")
    def _serialize_tier(self, value: ResponseTier) -> str:
        return value.name.lower()
