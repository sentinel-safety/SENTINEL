# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from shared.contracts.patterns import DetectRequest, DetectResponse
from shared.contracts.preprocess import ExtractedFeatures
from shared.patterns.matches import DetectionMode, PatternMatch
from shared.schemas.enums import EventType
from shared.schemas.event import Event
from shared.scoring.signals import SignalKind

pytestmark = pytest.mark.unit


def _req() -> DetectRequest:
    return DetectRequest(
        event=Event(
            id=uuid4(),
            tenant_id=uuid4(),
            actor_id=uuid4(),
            target_actor_ids=(uuid4(),),
            conversation_id=uuid4(),
            content_hash="a" * 64,
            type=EventType.MESSAGE,
            timestamp=datetime.now(UTC),
        ),
        features=ExtractedFeatures(
            normalized_content="don't tell",
            language="en",
            token_count=3,
            contains_url=False,
            contains_contact_request=False,
            minor_recipient=True,
            late_night_local=False,
        ),
    )


def test_detect_request_roundtrips_through_json() -> None:
    req = _req()
    as_json = req.model_dump(mode="json")
    reloaded = DetectRequest.model_validate(as_json)
    assert reloaded == req


def test_detect_response_defaults_to_empty_tuple() -> None:
    resp = DetectResponse()
    assert resp.matches == ()


def test_detect_response_carries_matches() -> None:
    match = PatternMatch(
        pattern_name="secrecy_request",
        signal_kind=SignalKind.SECRECY_REQUEST,
        confidence=1.0,
        evidence_excerpts=("don't tell",),
        detection_mode=DetectionMode.RULE,
        prompt_version=None,
    )
    resp = DetectResponse(matches=(match,))
    as_json = resp.model_dump(mode="json")
    reloaded = DetectResponse.model_validate(as_json)
    assert reloaded.matches[0].signal_kind is SignalKind.SECRECY_REQUEST
