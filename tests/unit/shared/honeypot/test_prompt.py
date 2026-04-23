# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.honeypot.personas import Persona
from shared.honeypot.prompt import build_steering_prompt

pytestmark = pytest.mark.unit


def _persona() -> Persona:
    return Persona(
        id="emma-13-us-east",
        age=13,
        gender="female",
        location="us-east",
        interests=("reading", "roblox", "art"),
        vocabulary_level="age_typical",
        regional_speech="us_east_suburban",
        consent_statement="SYNTHETIC — not a real child",
        activation_scope=("US",),
        prompt_version="v1",
    )


def test_prompt_contains_synthetic_marker() -> None:
    rendered = build_steering_prompt(persona=_persona(), conversation_excerpt=("hi",))
    assert "SYNTHETIC — not a real child" in rendered


def test_prompt_forbids_escalation_introduction() -> None:
    rendered = build_steering_prompt(persona=_persona(), conversation_excerpt=())
    assert "NEVER introduce sexual" in rendered
    assert "NEVER introduce age-specific" in rendered
    assert "NEVER introduce platform-migration" in rendered


def test_prompt_includes_anti_entrapment_rule() -> None:
    rendered = build_steering_prompt(persona=_persona(), conversation_excerpt=())
    assert "never escalate" in rendered.lower()
    assert "respond only" in rendered.lower()


def test_prompt_embeds_persona_attributes() -> None:
    rendered = build_steering_prompt(persona=_persona(), conversation_excerpt=())
    assert "age: 13" in rendered
    assert "interests: reading, roblox, art" in rendered
    assert "vocabulary_level: age_typical" in rendered
    assert "regional_speech: us_east_suburban" in rendered


def test_prompt_includes_conversation_excerpt() -> None:
    rendered = build_steering_prompt(
        persona=_persona(),
        conversation_excerpt=("actor: hey", "actor: how old r u"),
    )
    assert "actor: hey" in rendered
    assert "actor: how old r u" in rendered


def test_prompt_pins_prompt_version() -> None:
    rendered = build_steering_prompt(persona=_persona(), conversation_excerpt=())
    assert "prompt_version: v1" in rendered


def test_prompt_requires_disengagement_fallback() -> None:
    rendered = build_steering_prompt(persona=_persona(), conversation_excerpt=())
    assert "disengage" in rendered.lower()
    assert "off-platform" in rendered.lower()


def test_prompt_blocks_sharing_private_information() -> None:
    rendered = build_steering_prompt(persona=_persona(), conversation_excerpt=())
    assert "private information" in rendered.lower()
    assert "address" in rendered.lower()
