# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.scoring.aggregator import _is_qualifying
from shared.scoring.deltas import DELTA_BY_SIGNAL
from shared.scoring.signals import ScoreSignal, SignalKind

pytestmark = pytest.mark.unit


def test_federation_signal_match_kind_exists() -> None:
    assert SignalKind.FEDERATION_SIGNAL_MATCH.value == "federation_signal_match"


def test_federation_signal_match_delta() -> None:
    assert DELTA_BY_SIGNAL[SignalKind.FEDERATION_SIGNAL_MATCH] == 10


def test_federation_signal_match_is_qualifying() -> None:
    assert _is_qualifying(SignalKind.FEDERATION_SIGNAL_MATCH)


def test_federation_signal_match_constructs() -> None:
    signal = ScoreSignal(kind=SignalKind.FEDERATION_SIGNAL_MATCH, confidence=0.8)
    assert signal.kind is SignalKind.FEDERATION_SIGNAL_MATCH
