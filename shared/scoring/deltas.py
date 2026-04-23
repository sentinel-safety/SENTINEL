# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from typing import Final

from shared.scoring.signals import SignalKind

DELTA_BY_SIGNAL: Final[dict[SignalKind, int]] = {
    SignalKind.FRIENDSHIP_FORMING: 2,
    SignalKind.RISK_ASSESSMENT: 6,
    SignalKind.EXCLUSIVITY: 5,
    SignalKind.ISOLATION: 12,
    SignalKind.DESENSITIZATION: 15,
    SignalKind.SEXUAL_ESCALATION: 25,
    SignalKind.PERSONAL_INFO_PROBE: 8,
    SignalKind.PHOTO_REQUEST: 15,
    SignalKind.VIDEO_REQUEST: 20,
    SignalKind.PLATFORM_MIGRATION_REQUEST: 18,
    SignalKind.SECRECY_REQUEST: 20,
    SignalKind.GIFT_OFFERING: 12,
    SignalKind.COMPLIMENTS_QUESTIONS_ANOMALY: 5,
    SignalKind.LATE_NIGHT_MINOR_CONTACT: 3,
    SignalKind.RAPID_ESCALATION: 10,
    SignalKind.VERIFIED_POSITIVE_INTERACTION: -1,
    SignalKind.CLEAN_REVIEW: -3,
    SignalKind.CLEAN_VOLUME_THRESHOLD: -1,
    SignalKind.SELF_REPORTED_GOOD_CITIZENSHIP: -2,
    SignalKind.CROSS_SESSION_ESCALATION: 8,
    SignalKind.MULTI_MINOR_CONTACT_WINDOW: 10,
    SignalKind.BEHAVIORAL_FINGERPRINT_MATCH: 15,
    SignalKind.SUSPICIOUS_CLUSTER_MEMBERSHIP: 12,
    SignalKind.FEDERATION_SIGNAL_MATCH: 10,
}
