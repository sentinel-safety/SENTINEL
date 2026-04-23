# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from pydantic import Field, HttpUrl

from shared.schemas.base import FrozenModel, UtcDatetime
from shared.schemas.enums import ActionMode, ApiKeyScope, Jurisdiction, TenantTier


class ApiKey(FrozenModel):
    id: UUID
    tenant_id: UUID
    scope: ApiKeyScope
    hashed_value: str = Field(min_length=32, max_length=128)
    created_at: UtcDatetime
    last_used_at: UtcDatetime | None = None
    revoked_at: UtcDatetime | None = None

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None


class WebhookEndpoint(FrozenModel):
    id: UUID
    tenant_id: UUID
    url: HttpUrl
    events: tuple[str, ...] = Field(min_length=1)
    secret_hash: str = Field(min_length=32, max_length=128)
    active: bool = True
    created_at: UtcDatetime


class FeatureFlags(FrozenModel):
    federation_enabled: bool = False
    honeypot_enabled: bool = False
    honeypot_legal_review_acknowledged: bool = False
    action_mode: ActionMode = ActionMode.ADVISORY
    training_opt_in: bool = False


class Tenant(FrozenModel):
    id: UUID
    name: str = Field(min_length=1, max_length=200)
    tier: TenantTier = TenantTier.FREE
    compliance_jurisdictions: tuple[Jurisdiction, ...] = Field(default=(), min_length=0)
    data_retention_days: int = Field(default=30, ge=1, le=3650)
    feature_flags: FeatureFlags = Field(default_factory=FeatureFlags)
    api_keys: tuple[ApiKey, ...] = ()
    webhook_endpoints: tuple[WebhookEndpoint, ...] = ()
    created_at: UtcDatetime

    def active_api_keys(self) -> tuple[ApiKey, ...]:
        return tuple(k for k in self.api_keys if k.is_active)
