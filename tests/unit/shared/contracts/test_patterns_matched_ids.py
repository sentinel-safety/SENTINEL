# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import uuid4

import pytest

from shared.contracts.patterns import DetectResponse
from shared.patterns.matches import DetectionMode, PatternMatch
from shared.scoring.signals import SignalKind

pytestmark = pytest.mark.unit


def test_detect_response_default_matched_ids_is_empty() -> None:
    resp = DetectResponse()
    assert resp.matched_ids == ()


def test_detect_response_with_matched_ids_round_trips() -> None:
    match = PatternMatch(
        pattern_name="secrecy_request",
        signal_kind=SignalKind.SECRECY_REQUEST,
        confidence=1.0,
        evidence_excerpts=("don't tell",),
        detection_mode=DetectionMode.RULE,
        prompt_version=None,
    )
    ids = (uuid4(), uuid4())
    resp = DetectResponse(matches=(match,), matched_ids=ids)
    raw = resp.model_dump(mode="json")
    rebuilt = DetectResponse.model_validate(raw)
    assert rebuilt.matched_ids == ids
