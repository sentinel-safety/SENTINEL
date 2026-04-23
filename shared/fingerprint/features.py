# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from math import sqrt

from pydantic import Field, field_validator

from shared.schemas.base import FrozenModel

FINGERPRINT_DIM = 16


class ActorFeatureWindow(FrozenModel):
    total_messages: float = Field(ge=0.0)
    compliment_count: float = Field(ge=0.0)
    question_count: float = Field(ge=0.0)
    personal_info_requests: float = Field(ge=0.0)
    late_night_count: float = Field(ge=0.0)
    minor_recipient_count: float = Field(ge=0.0)
    platform_migration_mentions: float = Field(ge=0.0)
    secrecy_mentions: float = Field(ge=0.0)
    distinct_minor_targets: float = Field(ge=0.0)
    total_chars: float = Field(ge=0.0)
    distinct_conversations: float = Field(ge=0.0)
    url_mentions: float = Field(ge=0.0)
    gift_mentions: float = Field(ge=0.0)
    image_requests: float = Field(ge=0.0)
    video_requests: float = Field(ge=0.0)
    contact_requests: float = Field(ge=0.0)


class FingerprintVector(FrozenModel):
    values: tuple[float, ...]

    @field_validator("values")
    @classmethod
    def _validate_dim(cls, v: tuple[float, ...]) -> tuple[float, ...]:
        if len(v) != FINGERPRINT_DIM:
            raise ValueError(f"fingerprint must have {FINGERPRINT_DIM} dims, got {len(v)}")
        return v


def _safe_ratio(num: float, denom: float) -> float:
    return num / denom if denom > 0.0 else 0.0


def _scaled(count: float, scale: float) -> float:
    return min(count / scale, 1.0) if scale > 0.0 else 0.0


def compute_fingerprint(window: ActorFeatureWindow) -> tuple[float, ...]:
    n = window.total_messages
    if n == 0.0:
        return tuple(0.0 for _ in range(FINGERPRINT_DIM))
    raw: tuple[float, ...] = (
        _safe_ratio(window.compliment_count, n),
        _safe_ratio(window.question_count, n),
        _safe_ratio(window.personal_info_requests, n),
        _safe_ratio(window.late_night_count, n),
        _safe_ratio(window.minor_recipient_count, n),
        _safe_ratio(window.platform_migration_mentions, n),
        _safe_ratio(window.secrecy_mentions, n),
        _scaled(window.distinct_minor_targets, 10.0),
        _safe_ratio(window.total_chars, n * 280.0),
        _scaled(window.distinct_conversations, 20.0),
        _safe_ratio(window.url_mentions, n),
        _safe_ratio(window.gift_mentions, n),
        _safe_ratio(window.image_requests, n),
        _safe_ratio(window.video_requests, n),
        _safe_ratio(window.contact_requests, n),
        _scaled(n, 200.0),
    )
    norm = sqrt(sum(x * x for x in raw))
    if norm == 0.0:
        return tuple(0.0 for _ in range(FINGERPRINT_DIM))
    return tuple(x / norm for x in raw)
