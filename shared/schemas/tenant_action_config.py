# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from pydantic import Field

from shared.schemas.base import FrozenModel, UtcDatetime
from shared.schemas.enums import ActionMode


class TenantActionConfig(FrozenModel):
    tenant_id: UUID
    mode: ActionMode = ActionMode.ADVISORY
    action_overrides: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    webhook_secret: str = Field(min_length=32, max_length=128)
    created_at: UtcDatetime
    updated_at: UtcDatetime
