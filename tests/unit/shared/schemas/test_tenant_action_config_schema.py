# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from shared.schemas.enums import ActionMode
from shared.schemas.tenant_action_config import TenantActionConfig

pytestmark = pytest.mark.unit


def test_defaults_advisory_mode() -> None:
    now = datetime.now(UTC)
    cfg = TenantActionConfig(
        tenant_id=uuid4(),
        webhook_secret="a" * 64,  # pragma: allowlist secret
        created_at=now,
        updated_at=now,
    )
    assert cfg.mode == ActionMode.ADVISORY
    assert cfg.action_overrides == {}


def test_auto_enforce_mode() -> None:
    now = datetime.now(UTC)
    cfg = TenantActionConfig(
        tenant_id=uuid4(),
        mode=ActionMode.AUTO_ENFORCE,
        webhook_secret="b" * 64,  # pragma: allowlist secret
        created_at=now,
        updated_at=now,
    )
    assert cfg.mode == ActionMode.AUTO_ENFORCE


def test_overrides_accepts_tier_keys() -> None:
    now = datetime.now(UTC)
    cfg = TenantActionConfig(
        tenant_id=uuid4(),
        webhook_secret="c" * 64,  # pragma: allowlist secret
        action_overrides={"tier_3": ("review_queue",)},
        created_at=now,
        updated_at=now,
    )
    assert cfg.action_overrides["tier_3"] == ("review_queue",)


def test_webhook_secret_min_length() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValidationError):
        TenantActionConfig(
            tenant_id=uuid4(),
            webhook_secret="short",  # pragma: allowlist secret
            created_at=now,
            updated_at=now,
        )
