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

_FIXTURES = Path(__file__).parents[4] / "fixtures" / "patterns" / "desensitization"

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
    from services.patterns.app.library.desensitization import DesensitizationPattern

    p = DesensitizationPattern(provider=FakeProvider(responses={}))
    return p._render_prompt(text, history)


async def test_high_confidence_returns_match() -> None:
    text = "Have you ever seen adult stuff online? Everyone your age is curious about it, totally normal"
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.9,
                "evidence_excerpts": ["adult stuff online", "totally normal"],
            }
        }
    )
    from services.patterns.app.library.desensitization import DesensitizationPattern

    pattern = DesensitizationPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text))
    assert len(matches) == 1
    match = matches[0]
    assert match.pattern_name == "desensitization"
    assert match.signal_kind is SignalKind.DESENSITIZATION
    assert match.detection_mode is DetectionMode.LLM
    assert match.prompt_version == _PROMPT_VERSION
    assert match.confidence == pytest.approx(0.9)
    assert "adult stuff online" in match.evidence_excerpts


async def test_zero_confidence_returns_no_match() -> None:
    text = "what subjects do you like at school"
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.0,
                "evidence_excerpts": [],
            }
        }
    )
    from services.patterns.app.library.desensitization import DesensitizationPattern

    pattern = DesensitizationPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text))
    assert matches == ()


async def test_below_threshold_returns_no_match() -> None:
    text = "here's a joke, might be a bit edgy"
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.59,
                "evidence_excerpts": ["bit edgy"],
            }
        }
    )
    from services.patterns.app.library.desensitization import DesensitizationPattern

    pattern = DesensitizationPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text))
    assert matches == ()


async def test_at_threshold_returns_match() -> None:
    text = "okay this meme is a bit adult but you'll find it funny"
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.60,
                "evidence_excerpts": ["bit adult"],
            }
        }
    )
    from services.patterns.app.library.desensitization import DesensitizationPattern

    pattern = DesensitizationPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text))
    assert len(matches) == 1


async def test_does_not_fire_on_non_minor_recipient() -> None:
    text = "everyone watches that stuff, it's totally normal"
    from services.patterns.app.library.desensitization import DesensitizationPattern

    pattern = DesensitizationPattern(provider=FakeProvider(responses={}))
    matches = await pattern.detect_llm(_ctx(text, minor=False))
    assert matches == ()


async def test_pattern_metadata() -> None:
    from services.patterns.app.library.desensitization import DesensitizationPattern

    pattern = DesensitizationPattern(provider=FakeProvider(responses={}))
    assert pattern.name == "desensitization"
    assert pattern.signal_kind is SignalKind.DESENSITIZATION
    assert pattern.mode is DetectionMode.LLM


async def test_history_injected_into_prompt() -> None:
    text = "okay here's that adult meme I mentioned"
    history = ("hi", "want to see something funny")
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, history): {
                "confidence": 0.8,
                "evidence_excerpts": ["adult meme"],
            }
        }
    )
    from services.patterns.app.library.desensitization import DesensitizationPattern

    pattern = DesensitizationPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text, history=history))
    assert len(matches) == 1


@pytest.mark.parametrize("case", load_cases(_FIXTURES / "positive.yaml"), ids=lambda c: c.id)
async def test_positive_fixtures(case: FixtureCase) -> None:
    from services.patterns.app.library.desensitization import DesensitizationPattern

    text = " ".join(case.messages)
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.85,
                "evidence_excerpts": [case.messages[0][:40]],
            }
        }
    )
    pattern = DesensitizationPattern(provider=provider)
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
    from services.patterns.app.library.desensitization import DesensitizationPattern

    text = " ".join(case.messages)
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.0,
                "evidence_excerpts": [],
            }
        }
    )
    pattern = DesensitizationPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text, minor=case.minor_recipient))
    if case.expect_match:
        assert matches, f"fixture {case.id!r} expected match"
    else:
        assert matches == ()
