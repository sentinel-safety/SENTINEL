# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from services.patterns.app.library.gift_offering import GiftOfferingPattern
from services.patterns.app.library.late_night import LateNightPattern
from services.patterns.app.library.personal_info_probe import PersonalInfoProbePattern
from services.patterns.app.library.platform_migration import PlatformMigrationPattern
from services.patterns.app.library.secrecy_request import SecrecyRequestPattern
from shared.contracts.preprocess import ExtractedFeatures
from shared.explainability.evidence_templates import render_evidence
from shared.patterns.matches import PatternMatch
from shared.patterns.protocol import Pattern, SyncPatternContext
from shared.schemas.enums import EventType
from shared.schemas.event import Event

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _ctx(content: str, *, minor: bool = True, late_night: bool = False) -> SyncPatternContext:
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
        normalized_content=content,
        language="en",
        token_count=len(content.split()),
        contains_url=False,
        contains_contact_request=False,
        minor_recipient=minor,
        late_night_local=late_night,
    )
    return SyncPatternContext(event=event, features=features)


async def _run(pattern: Pattern, ctx: SyncPatternContext) -> tuple[PatternMatch, ...]:
    return await pattern.detect_sync(ctx)


async def test_secrecy_variables_render() -> None:
    matches = await _run(SecrecyRequestPattern(), _ctx("don't tell anyone"))
    assert matches[0].template_variables["matched_phrase"] == "don't tell"
    rendered = render_evidence(
        pattern_name="secrecy_request",
        variables=dict(matches[0].template_variables),
    )
    assert "don't tell" in rendered


async def test_platform_migration_variables_render() -> None:
    matches = await _run(PlatformMigrationPattern(), _ctx("let's move to telegram"))
    rendered = render_evidence(
        pattern_name="platform_migration",
        variables=dict(matches[0].template_variables),
    )
    assert "telegram" in rendered.lower()


async def test_personal_info_probe_variables_render() -> None:
    matches = await _run(PersonalInfoProbePattern(), _ctx("what school do you go to"))
    rendered = render_evidence(
        pattern_name="personal_info_probe",
        variables=dict(matches[0].template_variables),
    )
    assert "school" in rendered.lower()


async def test_gift_offering_variables_render() -> None:
    matches = await _run(GiftOfferingPattern(), _ctx("i'll send you vbucks"))
    rendered = render_evidence(
        pattern_name="gift_offering",
        variables=dict(matches[0].template_variables),
    )
    assert (
        "vbucks" in rendered.lower()
        or "v-bucks" in rendered.lower()
        or "send you" in rendered.lower()
    )


async def test_late_night_variables_render_without_vars() -> None:
    matches = await _run(LateNightPattern(), _ctx("hello", late_night=True))
    rendered = render_evidence(
        pattern_name="late_night",
        variables=dict(matches[0].template_variables),
    )
    assert "late" in rendered.lower()
