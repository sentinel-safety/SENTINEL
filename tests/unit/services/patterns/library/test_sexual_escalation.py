# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from tests.fixtures.patterns._loader import FixtureCase, load_cases

from shared.contracts.preprocess import ExtractedFeatures
from shared.llm import FakeProvider
from shared.patterns import DetectionMode, LLMPatternContext
from shared.schemas.enums import EventType
from shared.schemas.event import Event
from shared.scoring.signals import SignalKind

_FIXTURES = Path(__file__).parents[4] / "fixtures" / "patterns" / "sexual_escalation"

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]

_PROMPT_VERSION = "v1"


def _event() -> Event:
    return Event(
        id=uuid4(),
        tenant_id=uuid4(),
        actor_id=uuid4(),
        target_actor_ids=(uuid4(),),
        conversation_id=uuid4(),
        content_hash="a" * 64,
        timestamp=datetime.now(UTC),
        type=EventType.MESSAGE,
    )


def _features(text: str, *, minor: bool = True) -> ExtractedFeatures:
    return ExtractedFeatures(
        normalized_content=text,
        language="en",
        token_count=len(text.split()),
        contains_url=False,
        contains_contact_request=False,
        minor_recipient=minor,
        late_night_local=False,
    )


def _ctx(text: str, *, minor: bool = True, history: tuple[str, ...] = ()) -> LLMPatternContext:
    return LLMPatternContext(
        event=_event(),
        features=_features(text, minor=minor),
        recent_messages=history,
    )


def _build_prompt_key(text: str, history: tuple[str, ...]) -> str:
    from services.patterns.app.library.sexual_escalation import SexualEscalationPattern

    p = SexualEscalationPattern(provider=FakeProvider(responses={}))
    return p._render_prompt(text, history)


async def test_high_confidence_returns_primary_match() -> None:
    text = "I think about you in a sexual way"
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.9,
                "evidence_excerpts": ["think about you in a sexual way"],
                "photo_request": False,
                "video_request": False,
            }
        }
    )
    from services.patterns.app.library.sexual_escalation import SexualEscalationPattern

    pattern = SexualEscalationPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text))
    assert len(matches) == 1
    match = matches[0]
    assert match.pattern_name == "sexual_escalation"
    assert match.signal_kind is SignalKind.SEXUAL_ESCALATION
    assert match.detection_mode is DetectionMode.LLM
    assert match.prompt_version == _PROMPT_VERSION
    assert match.confidence == pytest.approx(0.9)


async def test_photo_request_emits_secondary_match() -> None:
    text = "Send me a photo of yourself, just for me"
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.85,
                "evidence_excerpts": ["Send me a photo"],
                "photo_request": True,
                "video_request": False,
            }
        }
    )
    from services.patterns.app.library.sexual_escalation import SexualEscalationPattern

    pattern = SexualEscalationPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text))
    assert len(matches) == 2
    signal_kinds = {m.signal_kind for m in matches}
    assert SignalKind.SEXUAL_ESCALATION in signal_kinds
    assert SignalKind.PHOTO_REQUEST in signal_kinds
    photo_match = next(m for m in matches if m.signal_kind is SignalKind.PHOTO_REQUEST)
    assert photo_match.pattern_name == "sexual_escalation:photo_request"
    assert photo_match.confidence == pytest.approx(0.85)


async def test_video_request_emits_secondary_match() -> None:
    text = "Send me a video of yourself dancing"
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.8,
                "evidence_excerpts": ["Send me a video"],
                "photo_request": False,
                "video_request": True,
            }
        }
    )
    from services.patterns.app.library.sexual_escalation import SexualEscalationPattern

    pattern = SexualEscalationPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text))
    assert len(matches) == 2
    signal_kinds = {m.signal_kind for m in matches}
    assert SignalKind.SEXUAL_ESCALATION in signal_kinds
    assert SignalKind.VIDEO_REQUEST in signal_kinds
    video_match = next(m for m in matches if m.signal_kind is SignalKind.VIDEO_REQUEST)
    assert video_match.pattern_name == "sexual_escalation:video_request"


async def test_both_photo_and_video_request_emits_three_matches() -> None:
    text = "Send me photos and a video of yourself"
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.95,
                "evidence_excerpts": ["Send me photos and a video"],
                "photo_request": True,
                "video_request": True,
            }
        }
    )
    from services.patterns.app.library.sexual_escalation import SexualEscalationPattern

    pattern = SexualEscalationPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text))
    assert len(matches) == 3
    signal_kinds = {m.signal_kind for m in matches}
    assert SignalKind.SEXUAL_ESCALATION in signal_kinds
    assert SignalKind.PHOTO_REQUEST in signal_kinds
    assert SignalKind.VIDEO_REQUEST in signal_kinds


async def test_zero_confidence_returns_no_match() -> None:
    text = "how was school today"
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.0,
                "evidence_excerpts": [],
                "photo_request": False,
                "video_request": False,
            }
        }
    )
    from services.patterns.app.library.sexual_escalation import SexualEscalationPattern

    pattern = SexualEscalationPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text))
    assert matches == ()


async def test_below_threshold_returns_no_match() -> None:
    text = "you're pretty cute"
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.44,
                "evidence_excerpts": ["pretty cute"],
                "photo_request": False,
                "video_request": False,
            }
        }
    )
    from services.patterns.app.library.sexual_escalation import SexualEscalationPattern

    pattern = SexualEscalationPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text))
    assert matches == ()


async def test_at_threshold_returns_match() -> None:
    text = "you're very attractive for someone your age"
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.45,
                "evidence_excerpts": ["very attractive"],
                "photo_request": False,
                "video_request": False,
            }
        }
    )
    from services.patterns.app.library.sexual_escalation import SexualEscalationPattern

    pattern = SexualEscalationPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text))
    assert len(matches) == 1


async def test_does_not_fire_on_non_minor_recipient() -> None:
    text = "You're so attractive, I think about you sexually"
    from services.patterns.app.library.sexual_escalation import SexualEscalationPattern

    pattern = SexualEscalationPattern(provider=FakeProvider(responses={}))
    matches = await pattern.detect_llm(_ctx(text, minor=False))
    assert matches == ()


async def test_pattern_metadata() -> None:
    from services.patterns.app.library.sexual_escalation import SexualEscalationPattern

    pattern = SexualEscalationPattern(provider=FakeProvider(responses={}))
    assert pattern.name == "sexual_escalation"
    assert pattern.signal_kind is SignalKind.SEXUAL_ESCALATION
    assert pattern.mode is DetectionMode.LLM


async def test_history_injected_into_prompt() -> None:
    text = "you're so attractive"
    history = ("hi", "hey")
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, history): {
                "confidence": 0.8,
                "evidence_excerpts": ["so attractive"],
                "photo_request": False,
                "video_request": False,
            }
        }
    )
    from services.patterns.app.library.sexual_escalation import SexualEscalationPattern

    pattern = SexualEscalationPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text, history=history))
    assert len(matches) == 1


@pytest.mark.parametrize("case", load_cases(_FIXTURES / "positive.yaml"), ids=lambda c: c.id)
async def test_positive_fixtures(case: FixtureCase) -> None:
    from services.patterns.app.library.sexual_escalation import SexualEscalationPattern

    text = " ".join(case.messages)
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.85,
                "evidence_excerpts": [case.messages[0][:40]],
                "photo_request": False,
                "video_request": False,
            }
        }
    )
    pattern = SexualEscalationPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text, minor=case.minor_recipient))
    if case.expect_match:
        assert matches, f"fixture {case.id!r} expected match"
    else:
        assert matches == ()


@pytest.mark.parametrize(
    "case",
    load_cases(_FIXTURES / "negative.yaml"),
    ids=lambda c: c.id,
)
async def test_negative_fixtures(case: FixtureCase) -> None:
    from services.patterns.app.library.sexual_escalation import SexualEscalationPattern

    text = " ".join(case.messages)
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.0,
                "evidence_excerpts": [],
                "photo_request": False,
                "video_request": False,
            }
        }
    )
    pattern = SexualEscalationPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text, minor=case.minor_recipient))
    if case.expect_match:
        assert matches, f"fixture {case.id!r} expected match"
    else:
        assert matches == ()
