# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC

import pytest

from shared.contracts.preprocess import ExtractedFeatures
from shared.patterns import DetectionMode, PatternMatch
from shared.patterns.protocol import LLMPatternContext, Pattern, SyncPatternContext
from shared.schemas.event import Event
from shared.scoring.signals import SignalKind

pytestmark = pytest.mark.unit


def _event() -> Event:
    from datetime import datetime
    from uuid import uuid4

    from shared.schemas.enums import EventType

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


def _features() -> ExtractedFeatures:
    return ExtractedFeatures(
        normalized_content="hi",
        language="en",
        token_count=2,
        contains_url=False,
        contains_contact_request=False,
        minor_recipient=True,
        late_night_local=False,
    )


def test_sync_pattern_context_is_frozen() -> None:
    ctx = SyncPatternContext(event=_event(), features=_features())
    with pytest.raises(ValueError):
        ctx.features = _features()  # type: ignore[misc]


def test_llm_pattern_context_includes_recent_messages() -> None:
    ctx = LLMPatternContext(
        event=_event(),
        features=_features(),
        recent_messages=("hi", "hello"),
    )
    assert ctx.recent_messages == ("hi", "hello")


class _FakeRulePattern:
    name = "fake"
    signal_kind = SignalKind.SECRECY_REQUEST
    mode = DetectionMode.RULE

    async def detect_sync(self, ctx: SyncPatternContext) -> tuple[PatternMatch, ...]:
        return ()


def test_pattern_protocol_structural_check() -> None:
    pattern: Pattern = _FakeRulePattern()
    assert pattern.name == "fake"
