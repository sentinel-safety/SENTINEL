# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from shared.response.action_defaults import recommend_actions
from shared.schemas.enums import ActionMode, ResponseTier
from shared.schemas.response_action import ActionKind
from shared.schemas.tenant_action_config import TenantActionConfig

pytestmark = pytest.mark.unit


def _config_with_override(tier: str, kinds: tuple[str, ...]) -> TenantActionConfig:
    now = datetime.now(UTC)
    return TenantActionConfig(
        tenant_id=uuid4(),
        mode=ActionMode.AUTO_ENFORCE,
        webhook_secret="a" * 64,  # pragma: allowlist secret
        action_overrides={tier: kinds},
        created_at=now,
        updated_at=now,
    )


def test_override_replaces_default_set() -> None:
    cfg = _config_with_override("tier_3", ("review_queue",))
    actions = recommend_actions(ResponseTier.THROTTLE, cfg)
    assert tuple(a.kind for a in actions) == (ActionKind.REVIEW_QUEUE,)


def test_override_for_different_tier_does_not_affect() -> None:
    cfg = _config_with_override("tier_5", ("silent_log",))
    actions = recommend_actions(ResponseTier.THROTTLE, cfg)
    kinds = [a.kind for a in actions]
    assert ActionKind.THROTTLE_DM_TO_MINORS in kinds


def test_empty_override_yields_empty_tuple() -> None:
    cfg = _config_with_override("tier_4", ())
    actions = recommend_actions(ResponseTier.RESTRICT, cfg)
    assert actions == ()
