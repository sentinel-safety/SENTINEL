# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from services.response.app.action_builder import build_response_action
from shared.response.tier_change import TierChangeEvent
from shared.schemas.enums import ActionMode, ResponseTier
from shared.schemas.reasoning import Reasoning
from shared.schemas.response_action import ActionKind
from shared.schemas.tenant_action_config import TenantActionConfig

pytestmark = pytest.mark.unit


def _config() -> TenantActionConfig:
    now = datetime.now(UTC)
    return TenantActionConfig(
        tenant_id=uuid4(),
        mode=ActionMode.AUTO_ENFORCE,
        webhook_secret="a" * 64,
        created_at=now,
        updated_at=now,
    )


def _change(new_tier: ResponseTier = ResponseTier.RESTRICT) -> TierChangeEvent:
    return TierChangeEvent(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        event_id=uuid4(),
        previous_tier=ResponseTier.THROTTLE,
        new_tier=new_tier,
        new_score=80,
        triggered_at=datetime.now(UTC),
    )


def _reasoning(evt: TierChangeEvent) -> Reasoning:
    return Reasoning(
        actor_id=evt.actor_id,
        tenant_id=evt.tenant_id,
        score_change=15,
        new_score=evt.new_score,
        new_tier=evt.new_tier,
        generated_at=evt.triggered_at,
    )


def test_action_builder_populates_actions() -> None:
    evt = _change()
    cfg = _config()
    action = build_response_action(
        event=evt,
        config=cfg,
        reasoning=_reasoning(evt),
    )
    kinds = [a.kind for a in action.actions]
    assert ActionKind.BLOCK_DM_TO_MINORS in kinds
    assert action.tier == evt.new_tier
    assert action.triggered_by_event_id == evt.event_id
