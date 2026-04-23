# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from typing import Final

from shared.schemas.enums import ResponseTier
from shared.schemas.response_action import ActionKind, RecommendedAction
from shared.schemas.tenant_action_config import TenantActionConfig

_DEFAULTS: Final[dict[ResponseTier, tuple[RecommendedAction, ...]]] = {
    ResponseTier.TRUSTED: (),
    ResponseTier.WATCH: (
        RecommendedAction(kind=ActionKind.SILENT_LOG, description="capture full event stream"),
    ),
    ResponseTier.ACTIVE_MONITOR: (
        RecommendedAction(
            kind=ActionKind.REVIEW_QUEUE,
            description="route minor messages to moderator queue",
        ),
    ),
    ResponseTier.THROTTLE: (
        RecommendedAction(
            kind=ActionKind.THROTTLE_DM_TO_MINORS,
            description="rate limit dms to minors",
        ),
        RecommendedAction(
            kind=ActionKind.DISABLE_MEDIA_TO_MINORS,
            description="block images and video to minors",
        ),
        RecommendedAction(
            kind=ActionKind.REQUIRE_APPROVAL_TO_FRIEND_MINOR,
            description="require human approval to friend new minors",
        ),
    ),
    ResponseTier.RESTRICT: (
        RecommendedAction(
            kind=ActionKind.BLOCK_DM_TO_MINORS,
            description="block all dms to minors",
        ),
        RecommendedAction(
            kind=ActionKind.RESTRICT_TO_PUBLIC_POSTS,
            description="restrict account to public posts",
        ),
        RecommendedAction(
            kind=ActionKind.REVIEW_QUEUE,
            description="mod review required for any minor interaction",
        ),
        RecommendedAction(
            kind=ActionKind.ACCOUNT_WARNING,
            description="issue account-level warning",
        ),
    ),
    ResponseTier.CRITICAL: (
        RecommendedAction(
            kind=ActionKind.SUSPEND,
            description="suspend account pending human review within one hour",
        ),
        RecommendedAction(
            kind=ActionKind.MANDATORY_REPORT,
            description="escalate to mandated reporting body per jurisdiction",
        ),
    ),
}


def _tier_key(tier: ResponseTier) -> str:
    return f"tier_{int(tier)}"


def recommend_actions(
    tier: ResponseTier,
    config: TenantActionConfig,
) -> tuple[RecommendedAction, ...]:
    defaults = _DEFAULTS[tier]
    override_keys = config.action_overrides.get(_tier_key(tier))
    if override_keys is None:
        return defaults
    kinds = tuple(ActionKind(k) for k in override_keys)
    return tuple(
        RecommendedAction(kind=k, description=f"tenant override for tier {int(tier)}")
        for k in kinds
    )
