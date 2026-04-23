# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


"""Scoring constants lifted verbatim from SENTINEL_SPECIFICATION section 5.

Any change to these numbers is a behavior change. Update the spec, write an
ADR, and expect a wave of test fixture updates.
"""

from __future__ import annotations

from typing import Final

MIN_SCORE: Final[int] = 0
MAX_SCORE: Final[int] = 100
NEW_ACCOUNT_BASELINE_SCORE: Final[int] = 5

GROOMING_FRIENDSHIP_FORMING_DELTA: Final[int] = 2
GROOMING_RISK_ASSESSMENT_DELTA: Final[int] = 6
GROOMING_EXCLUSIVITY_DELTA: Final[int] = 5
GROOMING_ISOLATION_DELTA: Final[int] = 12
GROOMING_DESENSITIZATION_DELTA: Final[int] = 15
GROOMING_SEXUAL_ESCALATION_DELTA: Final[int] = 25

PERSONAL_INFO_REQUEST_DELTA: Final[int] = 8
PHOTO_REQUEST_DELTA: Final[int] = 15
VIDEO_REQUEST_DELTA: Final[int] = 20
PLATFORM_MIGRATION_REQUEST_DELTA: Final[int] = 18
SECRECY_REQUEST_DELTA: Final[int] = 20
GIFT_OFFERING_DELTA: Final[int] = 12
COMPLIMENT_QUESTION_RATIO_ANOMALY_DELTA: Final[int] = 5
LATE_NIGHT_MINOR_CONTACT_DELTA: Final[int] = 3
RAPID_ESCALATION_DELTA: Final[int] = 10

MULTI_MINOR_CONTACT_DELTA: Final[int] = 10
BEHAVIORAL_FINGERPRINT_MATCH_DELTA: Final[int] = 15
SUSPICIOUS_CLUSTER_DELTA: Final[int] = 12
FEDERATION_SIGNAL_DELTA: Final[int] = 10

VOCAB_INCONGRUENCE_DELTA: Final[int] = 5
CULTURAL_REF_INCONGRUENCE_DELTA: Final[int] = 5
TYPING_PATTERN_INCONGRUENCE_DELTA: Final[int] = 3

VERIFIED_POSITIVE_DELTA: Final[int] = -1
CLEAN_MOD_REVIEW_DELTA: Final[int] = -3
CLEAN_VOLUME_THRESHOLD_DELTA: Final[int] = -1
USER_REPORT_CITIZENSHIP_DELTA: Final[int] = -2

DECAY_PER_WEEK: Final[int] = -1
DECAY_PERIOD_DAYS: Final[int] = 7
HIGH_TIER_DECAY_RATE_MULTIPLIER: Final[float] = 0.5
MINIMUM_SCORE_FLOOR: Final[int] = 5
MAJOR_EVENT_DECAY_SUSPEND_DAYS: Final[int] = 30
HIGH_TIER_DECAY_THRESHOLD: Final[int] = 60

FIRST_PASS_LATENCY_P99_MS: Final[int] = 50
FULL_PIPELINE_LATENCY_P99_MS: Final[int] = 800


def clamp_score(score: int) -> int:
    return max(MIN_SCORE, min(MAX_SCORE, score))
