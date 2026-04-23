# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from shared.explainability.reasoning_generator import generate_reasoning
from shared.graph.views import ContactGraphView
from shared.patterns.matches import DetectionMode, PatternMatch
from shared.schemas.enums import ResponseTier
from shared.scoring.signals import SignalKind

pytestmark = pytest.mark.unit


def _match() -> PatternMatch:
    return PatternMatch(
        pattern_name="platform_migration",
        signal_kind=SignalKind.PLATFORM_MIGRATION_REQUEST,
        confidence=0.91,
        evidence_excerpts=("let's move to telegram",),
        detection_mode=DetectionMode.RULE,
        prompt_version=None,
        template_variables={"matched_phrase": "let's move to telegram"},
    )


def test_happy_path_builds_reasoning() -> None:
    tenant = uuid.uuid4()
    actor = uuid.uuid4()
    now = datetime.now(UTC)
    r = generate_reasoning(
        actor_id=actor,
        tenant_id=tenant,
        previous_score=46,
        new_score=64,
        new_tier=ResponseTier.THROTTLE,
        matches=(_match(),),
        contact_graph=ContactGraphView(
            distinct_contacts_total=20,
            distinct_minor_contacts_window=7,
            contact_velocity_per_day=0.5,
            age_band_distribution={"13_15": 7},
            lookback_days=14,
        ),
        actor_memory=None,
        actor_age_days=18,
        action_kinds=("throttle_dm_to_minors", "review_queue"),
        generated_at=now,
    )
    assert r.actor_id == actor
    assert r.tenant_id == tenant
    assert r.score_change == 18
    assert r.new_score == 64
    assert r.new_tier == ResponseTier.THROTTLE
    assert r.primary_drivers[0].pattern == "Platform Migration Request"
    assert r.primary_drivers[0].pattern_id == "platform_migration"
    assert "telegram" in r.primary_drivers[0].evidence.lower()
    assert "7 distinct minor" in r.context
    assert "18" in r.context
    assert "throttle_dm_to_minors" in r.recommended_action_summary
    assert r.next_review_at is not None


def test_empty_matches_still_returns_reasoning() -> None:
    tenant = uuid.uuid4()
    actor = uuid.uuid4()
    now = datetime.now(UTC)
    r = generate_reasoning(
        actor_id=actor,
        tenant_id=tenant,
        previous_score=5,
        new_score=25,
        new_tier=ResponseTier.WATCH,
        matches=(),
        contact_graph=None,
        actor_memory=None,
        actor_age_days=None,
        action_kinds=(),
        generated_at=now,
    )
    assert r.primary_drivers == ()
    assert r.context == ""
    assert r.recommended_action_summary == ""
    assert r.next_review_at is None
    assert r.score_change == 20
