# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


"""Shared Pydantic schemas used across services.

These are the contract layer. Every service imports from here; no service
redefines these models. Changes are breaking changes — bump the minor version
of the shared package and document in an ADR.
"""

from shared.schemas.actor import Actor
from shared.schemas.audit_log import GENESIS_HASH, AuditEventType, AuditLogEntry
from shared.schemas.base import FrozenModel, MutableModel, UtcDatetime
from shared.schemas.conversation import Conversation
from shared.schemas.enums import (
    ActionMode,
    AgeBand,
    ApiKeyScope,
    ChannelType,
    EventType,
    GroomingStage,
    Jurisdiction,
    ResponseTier,
    TenantTier,
)
from shared.schemas.event import Event
from shared.schemas.pattern_match import PatternMatch
from shared.schemas.reasoning import PrimaryDriver, Reasoning
from shared.schemas.relationship_edge import RelationshipEdge
from shared.schemas.response_action import ActionKind, RecommendedAction, ResponseAction
from shared.schemas.suspicion_profile import ModeratorNote, ScoreHistoryEntry, SuspicionProfile
from shared.schemas.tenant import ApiKey, FeatureFlags, Tenant, WebhookEndpoint

__all__ = [
    "GENESIS_HASH",
    "ActionKind",
    "ActionMode",
    "Actor",
    "AgeBand",
    "ApiKey",
    "ApiKeyScope",
    "AuditEventType",
    "AuditLogEntry",
    "ChannelType",
    "Conversation",
    "Event",
    "EventType",
    "FeatureFlags",
    "FrozenModel",
    "GroomingStage",
    "Jurisdiction",
    "ModeratorNote",
    "MutableModel",
    "PatternMatch",
    "PrimaryDriver",
    "Reasoning",
    "RecommendedAction",
    "RelationshipEdge",
    "ResponseAction",
    "ResponseTier",
    "ScoreHistoryEntry",
    "SuspicionProfile",
    "Tenant",
    "TenantTier",
    "UtcDatetime",
    "WebhookEndpoint",
]
