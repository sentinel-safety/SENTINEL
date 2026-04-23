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

_FIXTURES = Path(__file__).parents[4] / "fixtures" / "patterns" / "friendship_forming"

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
    from services.patterns.app.library.friendship_forming import FriendshipFormingPattern

    p = FriendshipFormingPattern(provider=FakeProvider(responses={}))
    return p._render_prompt(text, history)


async def test_high_confidence_returns_match() -> None:
    text = "I feel like I've known you forever, you're so mature for your age"
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.9,
                "evidence_excerpts": ["known you forever", "mature for your age"],
            }
        }
    )
    from services.patterns.app.library.friendship_forming import FriendshipFormingPattern

    pattern = FriendshipFormingPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text))
    assert len(matches) == 1
    match = matches[0]
    assert match.pattern_name == "friendship_forming"
    assert match.signal_kind is SignalKind.FRIENDSHIP_FORMING
    assert match.detection_mode is DetectionMode.LLM
    assert match.prompt_version == _PROMPT_VERSION
    assert match.confidence == pytest.approx(0.9)
    assert "known you forever" in match.evidence_excerpts


async def test_zero_confidence_returns_no_match() -> None:
    text = "how was school today"
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.0,
                "evidence_excerpts": [],
            }
        }
    )
    from services.patterns.app.library.friendship_forming import FriendshipFormingPattern

    pattern = FriendshipFormingPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text))
    assert matches == ()


async def test_below_threshold_returns_no_match() -> None:
    text = "you seem like a really nice person"
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.29,
                "evidence_excerpts": ["nice person"],
            }
        }
    )
    from services.patterns.app.library.friendship_forming import FriendshipFormingPattern

    pattern = FriendshipFormingPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text))
    assert matches == ()


async def test_at_threshold_returns_match() -> None:
    text = "we have such a special connection, I've never met anyone like you"
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.3,
                "evidence_excerpts": ["special connection"],
            }
        }
    )
    from services.patterns.app.library.friendship_forming import FriendshipFormingPattern

    pattern = FriendshipFormingPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text))
    assert len(matches) == 1


async def test_does_not_fire_on_non_minor_recipient() -> None:
    text = "I've known you forever, you're so mature"
    from services.patterns.app.library.friendship_forming import FriendshipFormingPattern

    pattern = FriendshipFormingPattern(provider=FakeProvider(responses={}))
    matches = await pattern.detect_llm(_ctx(text, minor=False))
    assert matches == ()


async def test_pattern_metadata() -> None:
    from services.patterns.app.library.friendship_forming import FriendshipFormingPattern

    provider = FakeProvider(responses={})
    pattern = FriendshipFormingPattern(provider=provider)
    assert pattern.name == "friendship_forming"
    assert pattern.signal_kind is SignalKind.FRIENDSHIP_FORMING
    assert pattern.mode is DetectionMode.LLM


async def test_history_injected_into_prompt() -> None:
    text = "you're so special"
    history = ("hi", "hello there")
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, history): {
                "confidence": 0.8,
                "evidence_excerpts": ["so special"],
            }
        }
    )
    from services.patterns.app.library.friendship_forming import FriendshipFormingPattern

    pattern = FriendshipFormingPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text, history=history))
    assert len(matches) == 1


@pytest.mark.parametrize("case", load_cases(_FIXTURES / "positive.yaml"), ids=lambda c: c.id)
async def test_positive_fixtures(case: FixtureCase) -> None:
    from services.patterns.app.library.friendship_forming import FriendshipFormingPattern

    text = " ".join(case.messages)
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.85,
                "evidence_excerpts": [case.messages[0][:40]],
            }
        }
    )
    pattern = FriendshipFormingPattern(provider=provider)
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
    from services.patterns.app.library.friendship_forming import FriendshipFormingPattern

    text = " ".join(case.messages)
    provider = FakeProvider(
        responses={
            _build_prompt_key(text, ()): {
                "confidence": 0.0,
                "evidence_excerpts": [],
            }
        }
    )
    pattern = FriendshipFormingPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text, minor=case.minor_recipient))
    if case.expect_match:
        assert matches, f"fixture {case.id!r} expected match"
    else:
        assert matches == ()
