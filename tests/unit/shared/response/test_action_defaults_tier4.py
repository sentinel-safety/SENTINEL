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


def _config() -> TenantActionConfig:
    now = datetime.now(UTC)
    return TenantActionConfig(
        tenant_id=uuid4(),
        mode=ActionMode.ADVISORY,
        webhook_secret="a" * 64,  # pragma: allowlist secret
        created_at=now,
        updated_at=now,
    )


def test_restrict_returns_expected_actions() -> None:
    actions = recommend_actions(ResponseTier.RESTRICT, _config())
    kinds = [a.kind for a in actions]
    assert ActionKind.BLOCK_DM_TO_MINORS in kinds
    assert ActionKind.RESTRICT_TO_PUBLIC_POSTS in kinds
    assert ActionKind.ACCOUNT_WARNING in kinds
