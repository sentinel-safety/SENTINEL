# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from shared.schemas import (
    ActionKind,
    PrimaryDriver,
    Reasoning,
    RecommendedAction,
    ResponseAction,
    ResponseTier,
)

pytestmark = pytest.mark.unit


def _reasoning() -> Reasoning:
    return Reasoning(
        actor_id=uuid4(),
        tenant_id=uuid4(),
        score_change=0,
        new_score=5,
        new_tier=ResponseTier.TRUSTED,
        primary_drivers=(),
        generated_at=datetime.now(UTC),
    )


def test_response_action_defaults_delivery_fields_none() -> None:
    ra = ResponseAction(
        id=uuid4(),
        tenant_id=uuid4(),
        actor_id=uuid4(),
        tier=ResponseTier.WATCH,
        actions=(
            RecommendedAction(
                kind=ActionKind.SILENT_LOG, description="Log only; no user-facing change."
            ),
        ),
        triggered_at=datetime.now(UTC),
        reasoning=_reasoning(),
    )
    assert ra.delivered_to_platform_at is None
    assert ra.acknowledged_by_platform_at is None


def test_response_action_roundtrip() -> None:
    driver = PrimaryDriver(
        pattern="Secrecy Request",
        pattern_id="secrecy_request",
        confidence=0.8,
        evidence="Actor asked target not to tell their parents.",
    )
    reasoning = Reasoning(
        actor_id=uuid4(),
        tenant_id=uuid4(),
        score_change=20,
        new_score=45,
        new_tier=ResponseTier.ACTIVE_MONITOR,
        primary_drivers=(driver,),
        generated_at=datetime.now(UTC),
    )
    ra = ResponseAction(
        id=uuid4(),
        tenant_id=reasoning.tenant_id,
        actor_id=reasoning.actor_id,
        tier=ResponseTier.ACTIVE_MONITOR,
        actions=(
            RecommendedAction(
                kind=ActionKind.REVIEW_QUEUE,
                description="Queue minor-facing messages for mod review.",
                parameters={"window_hours": 24},
            ),
        ),
        triggered_at=datetime.now(UTC),
        reasoning=reasoning,
    )
    restored = ResponseAction.model_validate(ra.model_dump(mode="json"))
    assert restored == ra
