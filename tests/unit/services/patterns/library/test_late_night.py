# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from services.patterns.app.library.late_night import LateNightPattern
from shared.contracts.preprocess import ExtractedFeatures
from shared.patterns import SyncPatternContext
from shared.schemas.enums import EventType
from shared.schemas.event import Event
from shared.scoring.signals import SignalKind

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _ctx(*, minor: bool, late: bool) -> SyncPatternContext:
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
            normalized_content="anything",
            language="en",
            token_count=1,
            contains_url=False,
            contains_contact_request=False,
            minor_recipient=minor,
            late_night_local=late,
        ),
    )


async def test_fires_only_when_minor_and_late() -> None:
    pattern = LateNightPattern()
    assert len(await pattern.detect_sync(_ctx(minor=True, late=True))) == 1


@pytest.mark.parametrize(("minor", "late"), [(False, True), (True, False), (False, False)])
async def test_no_fire_otherwise(minor: bool, late: bool) -> None:
    pattern = LateNightPattern()
    assert await pattern.detect_sync(_ctx(minor=minor, late=late)) == ()


async def test_signal_kind_is_late_night() -> None:
    pattern = LateNightPattern()
    matches = await pattern.detect_sync(_ctx(minor=True, late=True))
    assert matches[0].signal_kind is SignalKind.LATE_NIGHT_MINOR_CONTACT
