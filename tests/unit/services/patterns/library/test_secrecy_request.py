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

from services.patterns.app.library.secrecy_request import SecrecyRequestPattern
from shared.contracts.preprocess import ExtractedFeatures
from shared.patterns import DetectionMode, SyncPatternContext
from shared.schemas.enums import EventType
from shared.schemas.event import Event
from shared.scoring.signals import SignalKind

_FIXTURES = Path(__file__).parents[4] / "fixtures" / "patterns" / "secrecy_request"

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _ctx(text: str, *, minor: bool = True) -> SyncPatternContext:
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
            minor_recipient=minor,
            late_night_local=False,
        ),
    )


async def test_fires_on_dont_tell() -> None:
    pattern = SecrecyRequestPattern()
    matches = await pattern.detect_sync(_ctx("don't tell your parents"))
    assert len(matches) == 1
    m = matches[0]
    assert m.signal_kind is SignalKind.SECRECY_REQUEST
    assert m.confidence == 1.0
    assert m.detection_mode is DetectionMode.RULE
    assert m.prompt_version is None


async def test_fires_on_keep_this_a_secret() -> None:
    pattern = SecrecyRequestPattern()
    matches = await pattern.detect_sync(_ctx("just keep this a secret between us"))
    assert len(matches) == 1


async def test_does_not_fire_on_unrelated_text() -> None:
    pattern = SecrecyRequestPattern()
    matches = await pattern.detect_sync(_ctx("hello how are you today"))
    assert matches == ()


async def test_metadata() -> None:
    pattern = SecrecyRequestPattern()
    assert pattern.name == "secrecy_request"
    assert pattern.signal_kind is SignalKind.SECRECY_REQUEST
    assert pattern.mode is DetectionMode.RULE


@pytest.mark.parametrize("case", load_cases(_FIXTURES / "positive.yaml"), ids=lambda c: c.id)
async def test_positive_fixtures_fire(case: FixtureCase) -> None:
    pattern = SecrecyRequestPattern()
    combined = " ".join(case.messages)
    matches = await pattern.detect_sync(_ctx(combined, minor=case.minor_recipient))
    if case.expect_match:
        assert matches, f"fixture {case.id} expected match, got none"
    else:
        assert matches == ()


@pytest.mark.parametrize(
    "case",
    load_cases(_FIXTURES / "negative.yaml") + load_cases(_FIXTURES / "adversarial.yaml"),
    ids=lambda c: c.id,
)
async def test_negative_and_adversarial_fixtures(case: FixtureCase) -> None:
    pattern = SecrecyRequestPattern()
    combined = " ".join(case.messages)
    matches = await pattern.detect_sync(_ctx(combined, minor=case.minor_recipient))
    if case.expect_match:
        assert matches, f"fixture {case.id} expected match, got none"
    else:
        assert matches == ()
