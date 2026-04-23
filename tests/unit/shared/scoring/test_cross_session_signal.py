# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.scoring.deltas import DELTA_BY_SIGNAL
from shared.scoring.signals import ScoreSignal, SignalKind

pytestmark = pytest.mark.unit


def test_cross_session_escalation_kind_exists() -> None:
    assert SignalKind.CROSS_SESSION_ESCALATION.value == "cross_session_escalation"


def test_cross_session_escalation_delta_is_eight() -> None:
    assert DELTA_BY_SIGNAL[SignalKind.CROSS_SESSION_ESCALATION] == 8


def test_cross_session_escalation_signal_constructs() -> None:
    signal = ScoreSignal(
        kind=SignalKind.CROSS_SESSION_ESCALATION,
        confidence=0.75,
        evidence="4 distinct conversations over 14 days",
    )
    assert signal.kind is SignalKind.CROSS_SESSION_ESCALATION
    assert signal.confidence == 0.75
