# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from enum import StrEnum


class Topic(StrEnum):
    EVENT_INGESTED = "event.ingested"
    EVENT_PREPROCESSED = "event.preprocessed"
    EVENT_CLASSIFIED = "event.classified"
    EVENT_SCORED = "event.scored"
    PATTERN_MATCHED = "pattern.matched"
    PROFILE_TIER_CHANGED = "profile.tier_changed"
    ACTION_RECOMMENDED = "action.recommended"
    MANDATORY_REPORT_REQUIRED = "mandatory_report.required"
    AUDIT_APPEND = "audit.append"
    WEBHOOK_DELIVER = "webhook.deliver"
    WEBHOOK_DLQ = "webhook.dlq"
    FEDERATION_OUTBOUND = "federation.outbound"
    FEDERATION_INBOUND = "federation.inbound"
