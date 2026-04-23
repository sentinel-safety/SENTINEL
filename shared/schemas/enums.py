# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from enum import IntEnum, StrEnum


class TenantTier(StrEnum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class ApiKeyScope(StrEnum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class Jurisdiction(StrEnum):
    US = "US"
    EU = "EU"
    UK = "UK"
    CA = "CA"
    AU = "AU"
    OTHER = "OTHER"


class ActionMode(StrEnum):
    ADVISORY = "advisory"
    AUTO_ENFORCE = "auto_enforce"


class AgeBand(StrEnum):
    UNDER_13 = "under_13"
    BAND_13_15 = "13_15"
    BAND_16_17 = "16_17"
    ADULT = "18_plus"
    UNKNOWN = "unknown"


class ChannelType(StrEnum):
    DM = "DM"
    GROUP = "group"
    PUBLIC = "public"
    VOICE_TRANSCRIPT = "voice_transcript"


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


class GroomingStage(StrEnum):
    FRIENDSHIP_FORMING = "friendship_forming"
    RISK_ASSESSMENT = "risk_assessment"
    EXCLUSIVITY = "exclusivity"
    ISOLATION = "isolation"
    DESENSITIZATION = "desensitization"
    SEXUAL_ESCALATION = "sexual_escalation"
