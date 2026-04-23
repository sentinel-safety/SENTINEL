# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from shared.contracts.classify import ClassifyRequest, ClassifyResponse
from shared.contracts.ingest import IngestEventRequest, IngestEventResponse
from shared.contracts.preprocess import (
    ExtractedFeatures,
    PreprocessRequest,
    PreprocessResponse,
)
from shared.contracts.score import ScoreRequest, ScoreResponse
from shared.schemas.enums import EventType, ResponseTier
from shared.schemas.event import Event
from shared.scoring.signals import ScoreSignal, SignalKind

pytestmark = pytest.mark.unit


def _event() -> Event:
    return Event(
        id=uuid4(),
        tenant_id=uuid4(),
        conversation_id=uuid4(),
        actor_id=uuid4(),
        timestamp=datetime.now(UTC),
        type=EventType.MESSAGE,
        content_hash="a" * 64,
    )


def test_ingest_request_normalizes_to_event_shape() -> None:
    req = IngestEventRequest(
        idempotency_key="abc-123",
        tenant_id=uuid4(),
        actor_external_id_hash="a" * 64,
        conversation_id=uuid4(),
        target_actor_external_id_hashes=("b" * 64,),
        event_type=EventType.MESSAGE,
        timestamp=datetime.now(UTC),
        content="Hello there",
        metadata={"platform": "mygame"},
    )
    assert req.content == "Hello there"


def test_ingest_response_includes_score_and_tier() -> None:
    resp = IngestEventResponse(
        event_id=uuid4(),
        current_score=42,
        tier=ResponseTier.ACTIVE_MONITOR,
        delta=+5,
    )
    assert resp.tier is ResponseTier.ACTIVE_MONITOR


def test_preprocess_request_carries_event_and_text() -> None:
    PreprocessRequest(event=_event(), content="Hi")


def test_preprocess_response_carries_features() -> None:
    PreprocessResponse(
        features=ExtractedFeatures(
            normalized_content="hi",
            language="en",
            token_count=1,
            contains_url=False,
            contains_contact_request=False,
            minor_recipient=False,
            late_night_local=False,
        )
    )


def test_classify_request_carries_event_and_features() -> None:
    ClassifyRequest(
        event=_event(),
        features=ExtractedFeatures(
            normalized_content="hi",
            language="en",
            token_count=1,
            contains_url=False,
            contains_contact_request=False,
            minor_recipient=False,
            late_night_local=False,
        ),
    )


def test_classify_response_is_signal_tuple() -> None:
    ClassifyResponse(signals=(ScoreSignal(kind=SignalKind.SECRECY_REQUEST, confidence=1.0),))


def test_score_request_and_response() -> None:
    ScoreRequest(
        event=_event(),
        signals=(ScoreSignal(kind=SignalKind.SECRECY_REQUEST, confidence=1.0),),
    )
    ScoreResponse(current_score=42, previous_score=37, delta=5, tier=ResponseTier.ACTIVE_MONITOR)
