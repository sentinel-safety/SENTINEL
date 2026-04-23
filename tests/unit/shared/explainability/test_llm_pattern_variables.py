# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest

from services.patterns.app.library.desensitization import DesensitizationPattern
from services.patterns.app.library.exclusivity_llm import ExclusivityLLMPattern
from services.patterns.app.library.friendship_forming import FriendshipFormingPattern
from services.patterns.app.library.isolation import IsolationPattern
from services.patterns.app.library.risk_assessment import RiskAssessmentPattern
from services.patterns.app.library.sexual_escalation import SexualEscalationPattern
from shared.contracts.preprocess import ExtractedFeatures
from shared.explainability.evidence_templates import render_evidence
from shared.patterns.protocol import LLMPatternContext
from shared.schemas.enums import EventType
from shared.schemas.event import Event

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


class _Stub:
    def __init__(self, extras: dict[str, Any] | None = None) -> None:
        self.extras = extras or {}

    async def complete(self, *, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        return {
            "confidence": 0.9,
            "evidence_excerpts": ["you are so mature"],
            **self.extras,
        }


def _ctx() -> LLMPatternContext:
    event = Event(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        target_actor_ids=(uuid.uuid4(),),
        timestamp=datetime.now(UTC),
        type=EventType.MESSAGE,
        content_hash="a" * 64,
    )
    features = ExtractedFeatures(
        normalized_content="hello",
        language="en",
        token_count=1,
        contains_url=False,
        contains_contact_request=False,
        minor_recipient=True,
        late_night_local=False,
    )
    return LLMPatternContext(event=event, features=features, recent_messages=())


@pytest.mark.parametrize(
    ("pattern_cls", "pattern_name"),
    [
        (FriendshipFormingPattern, "friendship_forming"),
        (RiskAssessmentPattern, "risk_assessment"),
        (IsolationPattern, "isolation"),
        (DesensitizationPattern, "desensitization"),
        (ExclusivityLLMPattern, "exclusivity_llm"),
    ],
)
async def test_llm_pattern_variables_render(pattern_cls: Any, pattern_name: str) -> None:
    pattern = pattern_cls(provider=_Stub())
    matches = await pattern.detect_llm(_ctx())
    assert matches, f"pattern {pattern_name} returned no matches"
    out = render_evidence(
        pattern_name=pattern_name,
        variables=dict(matches[0].template_variables),
    )
    assert "mature" in out.lower()


async def test_sexual_escalation_sub_matches_have_variables() -> None:
    pattern = SexualEscalationPattern(
        provider=_Stub(extras={"photo_request": True, "video_request": True})
    )
    matches = await pattern.detect_llm(_ctx())
    names = [m.pattern_name for m in matches]
    assert "sexual_escalation" in names
    assert "sexual_escalation:photo_request" in names
    assert "sexual_escalation:video_request" in names
    for m in matches:
        out = render_evidence(
            pattern_name=m.pattern_name,
            variables=dict(m.template_variables),
        )
        assert out
