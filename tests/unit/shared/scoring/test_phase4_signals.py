# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.scoring.deltas import DELTA_BY_SIGNAL
from shared.scoring.signals import ScoreSignal, SignalKind

pytestmark = pytest.mark.unit


def test_multi_minor_contact_window_kind_exists() -> None:
    assert SignalKind.MULTI_MINOR_CONTACT_WINDOW.value == "multi_minor_contact_window"


def test_behavioral_fingerprint_match_kind_exists() -> None:
    assert SignalKind.BEHAVIORAL_FINGERPRINT_MATCH.value == "behavioral_fingerprint_match"


def test_suspicious_cluster_membership_kind_exists() -> None:
    assert SignalKind.SUSPICIOUS_CLUSTER_MEMBERSHIP.value == "suspicious_cluster_membership"


def test_phase4_deltas_match_spec() -> None:
    assert DELTA_BY_SIGNAL[SignalKind.MULTI_MINOR_CONTACT_WINDOW] == 10
    assert DELTA_BY_SIGNAL[SignalKind.BEHAVIORAL_FINGERPRINT_MATCH] == 15
    assert DELTA_BY_SIGNAL[SignalKind.SUSPICIOUS_CLUSTER_MEMBERSHIP] == 12


def test_phase4_signals_construct() -> None:
    for kind in (
        SignalKind.MULTI_MINOR_CONTACT_WINDOW,
        SignalKind.BEHAVIORAL_FINGERPRINT_MATCH,
        SignalKind.SUSPICIOUS_CLUSTER_MEMBERSHIP,
    ):
        signal = ScoreSignal(kind=kind, confidence=0.9, evidence="x")
        assert signal.kind is kind
