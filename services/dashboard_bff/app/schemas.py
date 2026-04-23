# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field

from shared.schemas.base import FrozenModel, MutableModel, UtcDatetime


class DashboardRole(StrEnum):
    ADMIN = "admin"
    MOD = "mod"
    VIEWER = "viewer"
    AUDITOR = "auditor"
    RESEARCHER = "researcher"


class SessionUser(FrozenModel):
    id: UUID
    tenant_id: UUID
    email: str
    role: DashboardRole
    display_name: str


class LoginRequest(FrozenModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class UserResponse(FrozenModel):
    id: UUID
    tenant_id: UUID
    email: str
    role: DashboardRole
    display_name: str
    last_login_at: UtcDatetime | None = None


class LoginResponse(FrozenModel):
    access_token: str
    refresh_token: str
    user: UserResponse


class RefreshRequest(FrozenModel):
    refresh_token: str = Field(min_length=8)


class RefreshResponse(FrozenModel):
    access_token: str


class AlertListItem(FrozenModel):
    actor_id: UUID
    current_score: int
    tier: int
    tier_entered_at: UtcDatetime
    last_updated: UtcDatetime
    claimed_age_band: str


class AlertListResponse(FrozenModel):
    alerts: tuple[AlertListItem, ...]


class ActorDetail(FrozenModel):
    actor_id: UUID
    tenant_id: UUID
    claimed_age_band: str
    account_created_at: UtcDatetime | None = None
    current_score: int | None = None
    tier: int | None = None
    tier_entered_at: UtcDatetime | None = None


class EventSummary(FrozenModel):
    id: UUID
    conversation_id: UUID
    timestamp: UtcDatetime
    type: str
    score_delta: int


class EventListResponse(FrozenModel):
    events: tuple[EventSummary, ...]


class ReasoningEntry(FrozenModel):
    id: UUID
    event_id: UUID | None = None
    reasoning_json: dict[str, Any]
    created_at: UtcDatetime


class ReasoningListResponse(FrozenModel):
    reasoning: tuple[ReasoningEntry, ...]


class InvestigationMessage(FrozenModel):
    event_id: UUID
    actor_id: UUID
    timestamp: UtcDatetime
    type: str
    content_features: dict[str, Any]


class InvestigationMessagesResponse(FrozenModel):
    messages: tuple[InvestigationMessage, ...]


class AuditEntryItem(FrozenModel):
    id: UUID
    sequence: int
    actor_id: UUID | None = None
    event_type: str
    details: dict[str, Any]
    timestamp: UtcDatetime
    entry_hash: str


class AuditEntryListResponse(FrozenModel):
    entries: tuple[AuditEntryItem, ...]


class BiasGroupRow(FrozenModel):
    group: str
    total_actors: int
    total_flagged: int
    flag_rate: float


class BiasAuditResponse(FrozenModel):
    group_by: str
    rows: tuple[BiasGroupRow, ...]


class ComplianceExportRequest(FrozenModel):
    from_date: UtcDatetime = Field(alias="from")
    to_date: UtcDatetime = Field(alias="to")
    categories: tuple[str, ...] = Field(min_length=1)
    format: str = Field(default="zip", pattern="^zip$")


class TenantSettings(MutableModel):
    name: str = Field(min_length=1, max_length=200)
    tier: str
    compliance_jurisdictions: tuple[str, ...] = ()
    data_retention_days: int = Field(ge=1, le=3650)


class TenantActionConfigResponse(MutableModel):
    mode: str = Field(pattern="^(advisory|auto_enforce)$")
    action_overrides: dict[str, tuple[str, ...]] = Field(default_factory=dict)


class WebhookCreateRequest(FrozenModel):
    url: str = Field(min_length=1, max_length=2000)
    events: tuple[str, ...] = Field(min_length=1)


class WebhookListItem(FrozenModel):
    id: UUID
    url: str
    events: tuple[str, ...]
    active: bool
    created_at: UtcDatetime


class WebhookCreateResponse(FrozenModel):
    webhook: WebhookListItem
    secret: str


class WebhookListResponse(FrozenModel):
    webhooks: tuple[WebhookListItem, ...]


class ApiKeyCreateRequest(FrozenModel):
    name: str = Field(min_length=1, max_length=200)
    scope: str = Field(pattern="^(read|write|admin)$")


class ApiKeySummary(FrozenModel):
    id: UUID
    name: str
    prefix: str
    scope: str
    created_at: UtcDatetime
    revoked_at: UtcDatetime | None = None
    last_used_at: UtcDatetime | None = None


class ApiKeyCreateResponse(FrozenModel):
    api_key: ApiKeySummary
    secret: str


class ApiKeyListResponse(FrozenModel):
    api_keys: tuple[ApiKeySummary, ...]


class HoneypotToggleRequest(FrozenModel):
    honeypot_enabled: bool
    legal_review_acknowledged: bool


class HoneypotEvidenceListItem(FrozenModel):
    id: UUID
    actor_id: UUID
    persona_id: str
    content_hash: str
    created_at: UtcDatetime


class HoneypotEvidenceListResponse(FrozenModel):
    evidence: tuple[HoneypotEvidenceListItem, ...]


class HoneypotEvidenceDetailResponse(FrozenModel):
    id: UUID
    actor_id: UUID
    persona_id: str
    content_hash: str
    created_at: UtcDatetime
    synthetic_persona: bool
    json_payload: dict[str, Any]


class FederationToggleRequest(FrozenModel):
    enabled: bool
    publish: bool
    subscribe: bool
    jurisdictions_filter: list[str]
    federation_acknowledgment: bool


class FederationSettingsResponse(FrozenModel):
    enabled: bool
    publish: bool
    subscribe: bool
    jurisdictions_filter: list[str]


class PublisherSnapshot(FrozenModel):
    tenant_id: UUID
    display_name: str
    reputation: int
    jurisdictions: list[str]
    revoked: bool


class PublisherListResponse(FrozenModel):
    publishers: tuple[PublisherSnapshot, ...]


class FalseSignalRequest(FrozenModel):
    signal_id: UUID
    reason: str


class BugReportIn(FrozenModel):
    reporter_email: str = Field(min_length=3, max_length=320)
    summary: str = Field(min_length=1, max_length=500)
    details: str = Field(min_length=1)
    severity: str = Field(pattern="^(low|medium|high|critical)$")


class BugReportOut(FrozenModel):
    id: UUID
    tenant_id: UUID
    reporter_email: str
    summary: str
    severity: str
    status: str
    received_at: UtcDatetime
    resolved_at: UtcDatetime | None = None


class BugReportPatch(MutableModel):
    status: str | None = Field(default=None, pattern="^(new|triaging|accepted|rejected|resolved)$")


class BugReportListResponse(FrozenModel):
    reports: tuple[BugReportOut, ...]
