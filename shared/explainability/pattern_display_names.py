# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from typing import Final

PATTERN_DISPLAY_NAMES: Final[dict[str, str]] = {
    "secrecy_request": "Secrecy Request",
    "platform_migration": "Platform Migration Request",
    "personal_info_probe": "Personal Information Probe",
    "gift_offering": "Gift Offering",
    "exclusivity": "Exclusivity Language",
    "exclusivity_llm": "Exclusivity Language (LLM)",
    "late_night": "Late-Night Minor Contact",
    "multi_minor_contact": "Multiple Minor Contacts In Window",
    "cross_session_escalation": "Cross-Session Escalation",
    "age_incongruence": "Age Incongruence",
    "behavioral_fingerprint_match": "Behavioral Fingerprint Match",
    "suspicious_cluster_membership": "Suspicious Cluster Membership",
    "friendship_forming": "Friendship Forming Stage",
    "risk_assessment": "Risk Assessment Stage",
    "isolation": "Isolation Stage",
    "desensitization": "Desensitization Stage",
    "sexual_escalation": "Sexual Escalation",
    "sexual_escalation:photo_request": "Photo Request",
    "sexual_escalation:video_request": "Video Request",
    "federation_signal_match": "Federated Signal Match",
}
