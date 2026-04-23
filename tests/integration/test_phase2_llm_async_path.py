# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from services.patterns.app.library.friendship_forming import FriendshipFormingPattern
from services.patterns.app.library.isolation import IsolationPattern
from services.patterns.app.library.risk_assessment import RiskAssessmentPattern
from services.patterns.app.registry import build_llm_patterns
from shared.contracts.preprocess import ExtractedFeatures
from shared.llm import FakeProvider
from shared.patterns import LLMPatternContext
from shared.schemas.enums import EventType
from shared.schemas.event import Event

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures" / "patterns"


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


def _build_prompt_key_friendship(text: str, history: tuple[str, ...]) -> str:
    p = FriendshipFormingPattern(provider=FakeProvider(responses={}))
    return p._render_prompt(text, history)


def _build_prompt_key_risk(text: str, history: tuple[str, ...]) -> str:
    p = RiskAssessmentPattern(provider=FakeProvider(responses={}))
    return p._render_prompt(text, history)


def _build_prompt_key_isolation(text: str, history: tuple[str, ...]) -> str:
    p = IsolationPattern(provider=FakeProvider(responses={}))
    return p._render_prompt(text, history)


async def test_friendship_forming_detects_grooming_message() -> None:
    text = "you're honestly so mature for your age, no one gets you like I do"
    provider = FakeProvider(
        responses={
            _build_prompt_key_friendship(text, ()): {
                "confidence": 0.85,
                "evidence_excerpts": ["mature for your age", "no one gets you like I do"],
            }
        }
    )
    pattern = FriendshipFormingPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text))
    assert len(matches) == 1
    assert matches[0].pattern_name == "friendship_forming"
    assert matches[0].confidence == pytest.approx(0.85)


async def test_friendship_forming_skips_non_minor() -> None:
    text = "i feel we have a special connection, no one understands me like you do"
    pattern = FriendshipFormingPattern(provider=FakeProvider(responses={}))
    matches = await pattern.detect_llm(_ctx(text, minor=False))
    assert matches == ()


async def test_risk_assessment_detects_parental_probe() -> None:
    text = "are your parents home right now or are you alone?"
    provider = FakeProvider(
        responses={
            _build_prompt_key_risk(text, ()): {
                "confidence": 0.90,
                "evidence_excerpts": ["parents home right now", "are you alone"],
            }
        }
    )
    pattern = RiskAssessmentPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text))
    assert len(matches) == 1
    assert matches[0].pattern_name == "risk_assessment"


async def test_isolation_detects_peer_separation() -> None:
    text = "those kids at school are so immature, you're different, I understand you"
    provider = FakeProvider(
        responses={
            _build_prompt_key_isolation(text, ()): {
                "confidence": 0.80,
                "evidence_excerpts": ["kids at school are so immature", "I understand you"],
            }
        }
    )
    pattern = IsolationPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text))
    assert len(matches) == 1
    assert matches[0].pattern_name == "isolation"


async def test_build_llm_patterns_returns_all_six() -> None:
    provider = FakeProvider(responses={})
    patterns = build_llm_patterns(provider)
    names = {p.name for p in patterns}
    assert names == {
        "friendship_forming",
        "risk_assessment",
        "isolation",
        "desensitization",
        "sexual_escalation",
        "exclusivity_llm",
    }


async def test_llm_patterns_skip_non_minor_uniformly() -> None:
    provider = FakeProvider(responses={})
    patterns = build_llm_patterns(provider)
    text = "let's keep this between us, no one would understand"
    for p in patterns:
        matches = await p.detect_llm(_ctx(text, minor=False))
        assert matches == (), f"{p.name} should skip non-minor recipient"


async def test_adversarial_emoji_fixture_friendship() -> None:
    text = "u r so 💯 mature 4 ur age... no1 gets u like i do 🥺"
    provider = FakeProvider(
        responses={
            _build_prompt_key_friendship(text, ()): {
                "confidence": 0.76,
                "evidence_excerpts": ["mature 4 ur age", "no1 gets u like i do"],
            }
        }
    )
    pattern = FriendshipFormingPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(text))
    assert len(matches) == 1


async def test_adversarial_split_messages_friendship() -> None:
    messages = ("i feel like", "we have such a", "special connection tbh")
    history = messages[:-1]
    current = messages[-1]
    provider = FakeProvider(
        responses={
            _build_prompt_key_friendship(current, history): {
                "confidence": 0.74,
                "evidence_excerpts": ["special connection"],
            }
        }
    )
    pattern = FriendshipFormingPattern(provider=provider)
    matches = await pattern.detect_llm(_ctx(current, history=history))
    assert len(matches) == 1
