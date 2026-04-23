# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from services.patterns.app.library.exclusivity import ExclusivityPattern
from shared.contracts.preprocess import ExtractedFeatures
from shared.patterns import SyncPatternContext
from shared.schemas.enums import EventType
from shared.schemas.event import Event
from shared.scoring.signals import SignalKind

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _ctx(text: str) -> SyncPatternContext:
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
            token_count=10,
            contains_url=False,
            contains_contact_request=False,
            minor_recipient=True,
            late_night_local=False,
        ),
    )


async def test_fires_on_exclusivity_phrase() -> None:
    pattern = ExclusivityPattern()
    matches = await pattern.detect_sync(_ctx("you are so mature for your age"))
    assert len(matches) == 1
    assert matches[0].signal_kind is SignalKind.EXCLUSIVITY


async def test_no_fire_on_safe() -> None:
    pattern = ExclusivityPattern()
    assert await pattern.detect_sync(_ctx("nice to meet you")) == ()
