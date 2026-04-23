# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.federation.reputation import ReputationDelta, adjust_reputation

pytestmark = pytest.mark.unit


def test_confirm_true_increments() -> None:
    assert adjust_reputation(50, "CONFIRM_TRUE") == 51


def test_confirm_false_decrements() -> None:
    assert adjust_reputation(50, "CONFIRM_FALSE") == 45


def test_explicit_complaint_decrements() -> None:
    assert adjust_reputation(50, "EXPLICIT_COMPLAINT") == 40


def test_signature_invalid_decrements() -> None:
    assert adjust_reputation(50, "SIGNATURE_INVALID") == 48


def test_clamps_at_100() -> None:
    assert adjust_reputation(99, "CONFIRM_TRUE") == 100
    assert adjust_reputation(100, "CONFIRM_TRUE") == 100


def test_clamps_at_0() -> None:
    assert adjust_reputation(1, "CONFIRM_FALSE") == 0
    assert adjust_reputation(0, "CONFIRM_FALSE") == 0


def test_delta_enum_values() -> None:
    assert int(ReputationDelta.CONFIRM_TRUE) == 1
    assert int(ReputationDelta.CONFIRM_FALSE) == -5
    assert int(ReputationDelta.EXPLICIT_COMPLAINT) == -10
    assert int(ReputationDelta.SIGNATURE_INVALID) == -2


def test_invalid_event_kind_raises() -> None:
    with pytest.raises(KeyError):
        adjust_reputation(50, "UNKNOWN_EVENT")
