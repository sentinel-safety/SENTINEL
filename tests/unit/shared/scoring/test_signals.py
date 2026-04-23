# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.scoring.signals import ScoreSignal, SignalKind

pytestmark = pytest.mark.unit


def test_signal_kind_covers_spec_section_5_2() -> None:
    expected = {
        "friendship_forming",
        "risk_assessment",
        "exclusivity",
        "isolation",
        "desensitization",
        "sexual_escalation",
        "personal_info_probe",
        "photo_request",
        "video_request",
        "platform_migration_request",
        "secrecy_request",
        "gift_offering",
        "compliments_questions_anomaly",
        "late_night_minor_contact",
        "rapid_escalation",
        "verified_positive_interaction",
        "clean_review",
        "clean_volume_threshold",
        "self_reported_good_citizenship",
        "cross_session_escalation",
        "multi_minor_contact_window",
        "behavioral_fingerprint_match",
        "suspicious_cluster_membership",
        "federation_signal_match",
    }
    assert {kind.value for kind in SignalKind} == expected


def test_score_signal_requires_confidence_in_unit_interval() -> None:
    with pytest.raises(ValueError):
        ScoreSignal(kind=SignalKind.SECRECY_REQUEST, confidence=1.1)


def test_score_signal_is_frozen() -> None:
    signal = ScoreSignal(kind=SignalKind.SECRECY_REQUEST, confidence=0.9)
    with pytest.raises(ValueError):
        signal.confidence = 0.5  # type: ignore[misc]
