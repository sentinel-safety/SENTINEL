# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from services.patterns.app.library.age_incongruence import AgeIncongruencePattern
from shared.contracts.preprocess import ExtractedFeatures
from shared.patterns import SyncPatternContext
from shared.patterns.matches import DetectionMode
from shared.schemas.enums import EventType
from shared.schemas.event import Event

pytestmark = pytest.mark.unit


def _ctx(text: str = "hello") -> SyncPatternContext:
    return SyncPatternContext(
        event=Event(
            id=uuid4(),
            tenant_id=uuid4(),
            actor_id=uuid4(),
            target_actor_ids=(uuid4(),),
            conversation_id=uuid4(),
            content_hash="a" * 64,
            timestamp=datetime.now(UTC),
            type=EventType.MESSAGE,
        ),
        features=ExtractedFeatures(
            normalized_content=text,
            language="en",
            token_count=1,
            contains_url=False,
            contains_contact_request=False,
            minor_recipient=True,
            late_night_local=False,
        ),
    )


@pytest.mark.asyncio
async def test_is_noop_always_returns_empty() -> None:
    pattern = AgeIncongruencePattern()
    assert await pattern.detect_sync(_ctx("you seem way older than your age")) == ()


@pytest.mark.asyncio
async def test_noop_on_safe_content() -> None:
    pattern = AgeIncongruencePattern()
    assert await pattern.detect_sync(_ctx("hello there")) == ()


def test_metadata() -> None:
    pattern = AgeIncongruencePattern()
    assert pattern.name == "age_incongruence"
    assert pattern.mode is DetectionMode.RULE
