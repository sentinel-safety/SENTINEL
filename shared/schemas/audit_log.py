# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import Field

from shared.schemas.base import FrozenModel, UtcDatetime


class AuditEventType(StrEnum):
    EVENT_SCORED = "event.scored"
    SCORE_CHANGED = "score.changed"
    TIER_CHANGED = "tier.changed"
    PATTERN_MATCHED = "pattern.matched"
    ACTION_RECOMMENDED = "action.recommended"
    ACTION_DELIVERED = "action.delivered"
    MOD_NOTE_ADDED = "mod.note_added"
    MOD_OVERRIDE = "mod.override"
    BREAK_GLASS_ACCESS = "break_glass.access"
    ACTOR_ERASED = "actor.erased"
    DATA_EXPORTED = "data.exported"
    TENANT_SETTING_CHANGED = "tenant.setting_changed"
    API_KEY_ROTATED = "api_key.rotated"  # pragma: allowlist secret
    WEBHOOK_DELIVERED = "webhook.delivered"
    WEBHOOK_FAILED = "webhook.failed"
    MANDATORY_REPORT_TRIGGERED = "mandatory_report.triggered"
    INVESTIGATION_CONTENT_ACCESS = "investigation.content_access"
    DASHBOARD_LOGIN = "dashboard.login"
    COMPLIANCE_EXPORTED = "compliance.exported"
    HONEYPOT_ACTIVATED = "honeypot.activated"
    HONEYPOT_DENIED = "honeypot.denied"
    HONEYPOT_EVIDENCE_PACKAGED = "honeypot.evidence_packaged"
    FEDERATION_PUBLISHED = "federation.published"
    FEDERATION_RECEIVED = "federation.received"


GENESIS_HASH: str = "0" * 64


class AuditLogEntry(FrozenModel):
    id: UUID
    tenant_id: UUID
    actor_id: UUID | None = None
    event_type: AuditEventType
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: UtcDatetime
    previous_entry_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    entry_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
