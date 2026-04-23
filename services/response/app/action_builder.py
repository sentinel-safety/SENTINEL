# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import uuid4

from shared.response.action_defaults import recommend_actions
from shared.response.tier_change import TierChangeEvent
from shared.schemas.reasoning import Reasoning
from shared.schemas.response_action import ResponseAction
from shared.schemas.tenant_action_config import TenantActionConfig


def build_response_action(
    *,
    event: TierChangeEvent,
    config: TenantActionConfig,
    reasoning: Reasoning,
) -> ResponseAction:
    actions = recommend_actions(event.new_tier, config)
    return ResponseAction(
        id=uuid4(),
        tenant_id=event.tenant_id,
        actor_id=event.actor_id,
        tier=event.new_tier,
        actions=actions,
        triggered_at=event.triggered_at,
        triggered_by_event_id=event.event_id,
        reasoning=reasoning,
    )
