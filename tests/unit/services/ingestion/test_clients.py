# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest

from services.ingestion.app.clients import DownstreamClients
from shared.config import Settings
from shared.contracts.patterns import DetectResponse
from shared.contracts.preprocess import ExtractedFeatures, PreprocessResponse
from shared.contracts.score import ScoreResponse
from shared.patterns.matches import DetectionMode, PatternMatch
from shared.schemas.enums import AgeBand, EventType, ResponseTier
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


def _features() -> ExtractedFeatures:
    return ExtractedFeatures(
        normalized_content="don't tell your parents",
        language="en",
        token_count=4,
        contains_url=False,
        contains_contact_request=False,
        minor_recipient=True,
        late_night_local=False,
    )


async def test_clients_preprocess_posts_to_configured_url() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/internal/preprocess"
        features = ExtractedFeatures(
            normalized_content="hi",
            language="en",
            token_count=1,
            contains_url=False,
            contains_contact_request=False,
            minor_recipient=True,
            late_night_local=False,
        )
        return httpx.Response(
            200, json=PreprocessResponse(features=features).model_dump(mode="json")
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://preprocess") as http:
        clients = DownstreamClients(
            settings=Settings(env="test"),
            http=http,
            preprocess_url="http://preprocess",
            patterns_url="http://patterns",
            score_url="http://score",
        )
        resp = await clients.preprocess(
            event=_event(),
            content="hi",
            recipient_age_bands=(AgeBand.UNDER_13,),
            recipient_timezone="UTC",
        )
    assert resp.features.minor_recipient is True


async def test_clients_detect_and_score_flow() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/internal/detect":
            match = PatternMatch(
                pattern_name="secrecy_request",
                signal_kind=SignalKind.SECRECY_REQUEST,
                confidence=1.0,
                evidence_excerpts=("don't tell your parents",),
                detection_mode=DetectionMode.RULE,
            )
            return httpx.Response(
                200,
                json=DetectResponse(matches=(match,)).model_dump(mode="json"),
            )
        if request.url.path == "/internal/score":
            return httpx.Response(
                200,
                json=ScoreResponse(
                    current_score=25,
                    previous_score=5,
                    delta=20,
                    tier=ResponseTier.WATCH,
                ).model_dump(mode="json"),
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport, base_url="http://x") as http:
        clients = DownstreamClients(
            settings=Settings(env="test"),
            http=http,
            preprocess_url="http://x",
            patterns_url="http://x",
            score_url="http://x",
        )
        detect_resp = await clients.detect(event=_event(), features=_features())
        score_resp = await clients.score(
            event=_event(),
            signals=(ScoreSignal(kind=SignalKind.SECRECY_REQUEST, confidence=1.0),),
        )
    assert len(detect_resp.matches) == 1
    assert detect_resp.matches[0].signal_kind is SignalKind.SECRECY_REQUEST
    assert score_resp.tier is ResponseTier.WATCH
