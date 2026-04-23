# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.scoring.deltas import DELTA_BY_SIGNAL
from shared.scoring.signals import SignalKind

pytestmark = pytest.mark.unit


def test_every_signal_has_a_delta() -> None:
    assert set(DELTA_BY_SIGNAL) == set(SignalKind)


@pytest.mark.parametrize(
    ("kind", "delta"),
    [
        (SignalKind.FRIENDSHIP_FORMING, 2),
        (SignalKind.RISK_ASSESSMENT, 6),
        (SignalKind.EXCLUSIVITY, 5),
        (SignalKind.ISOLATION, 12),
        (SignalKind.DESENSITIZATION, 15),
        (SignalKind.SEXUAL_ESCALATION, 25),
        (SignalKind.PERSONAL_INFO_PROBE, 8),
        (SignalKind.PHOTO_REQUEST, 15),
        (SignalKind.VIDEO_REQUEST, 20),
        (SignalKind.PLATFORM_MIGRATION_REQUEST, 18),
        (SignalKind.SECRECY_REQUEST, 20),
        (SignalKind.GIFT_OFFERING, 12),
        (SignalKind.COMPLIMENTS_QUESTIONS_ANOMALY, 5),
        (SignalKind.LATE_NIGHT_MINOR_CONTACT, 3),
        (SignalKind.RAPID_ESCALATION, 10),
        (SignalKind.VERIFIED_POSITIVE_INTERACTION, -1),
        (SignalKind.CLEAN_REVIEW, -3),
        (SignalKind.CLEAN_VOLUME_THRESHOLD, -1),
        (SignalKind.SELF_REPORTED_GOOD_CITIZENSHIP, -2),
    ],
)
def test_delta_matches_specification(kind: SignalKind, delta: int) -> None:
    assert DELTA_BY_SIGNAL[kind] == delta
