# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from enum import StrEnum

from pydantic import Field

from shared.schemas.base import FrozenModel


class SignalKind(StrEnum):
    FRIENDSHIP_FORMING = "friendship_forming"
    RISK_ASSESSMENT = "risk_assessment"
    EXCLUSIVITY = "exclusivity"
    ISOLATION = "isolation"
    DESENSITIZATION = "desensitization"
    SEXUAL_ESCALATION = "sexual_escalation"
    PERSONAL_INFO_PROBE = "personal_info_probe"
    PHOTO_REQUEST = "photo_request"
    VIDEO_REQUEST = "video_request"
    PLATFORM_MIGRATION_REQUEST = "platform_migration_request"
    SECRECY_REQUEST = "secrecy_request"
    GIFT_OFFERING = "gift_offering"
    COMPLIMENTS_QUESTIONS_ANOMALY = "compliments_questions_anomaly"
    LATE_NIGHT_MINOR_CONTACT = "late_night_minor_contact"
    RAPID_ESCALATION = "rapid_escalation"
    VERIFIED_POSITIVE_INTERACTION = "verified_positive_interaction"
    CLEAN_REVIEW = "clean_review"
    CLEAN_VOLUME_THRESHOLD = "clean_volume_threshold"
    SELF_REPORTED_GOOD_CITIZENSHIP = "self_reported_good_citizenship"
    CROSS_SESSION_ESCALATION = "cross_session_escalation"
    MULTI_MINOR_CONTACT_WINDOW = "multi_minor_contact_window"
    BEHAVIORAL_FINGERPRINT_MATCH = "behavioral_fingerprint_match"
    SUSPICIOUS_CLUSTER_MEMBERSHIP = "suspicious_cluster_membership"
    FEDERATION_SIGNAL_MATCH = "federation_signal_match"


class ScoreSignal(FrozenModel):
    kind: SignalKind
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: str = Field(default="", max_length=500)
