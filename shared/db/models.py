# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, BYTEA, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.db.base import Base, uuid_pk


class Tenant(Base):
    __tablename__ = "tenant"

    id: Mapped[UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    tier: Mapped[str] = mapped_column(String(20), nullable=False, default="free")
    compliance_jurisdictions: Mapped[list[Any]] = mapped_column(
        ARRAY(String(16)), nullable=False, server_default="{}"
    )
    data_retention_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    feature_flags: Mapped[dict[str, Any]] = mapped_column(
        nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    api_keys: Mapped[list[ApiKey]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )
    webhook_endpoints: Mapped[list[WebhookEndpoint]] = relationship(
        back_populates="tenant", cascade="all, delete-orphan"
    )


class ApiKey(Base):
    __tablename__ = "api_key"

    id: Mapped[UUID] = uuid_pk()
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    key_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    scope: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_used_at: Mapped[datetime | None] = mapped_column(nullable=True)

    tenant: Mapped[Tenant] = relationship(back_populates="api_keys")

    __table_args__ = (CheckConstraint("scope in ('read','write','admin')", name="scope_valid"),)


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoint"

    id: Mapped[UUID] = uuid_pk()
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    secret_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    subscribed_topics: Mapped[list[Any]] = mapped_column(
        ARRAY(String(64)), nullable=False, server_default="{}"
    )
    active: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))

    tenant: Mapped[Tenant] = relationship(back_populates="webhook_endpoints")


class Actor(Base):
    __tablename__ = "actor"

    id: Mapped[UUID] = uuid_pk()
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    external_id_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    claimed_age_band: Mapped[str] = mapped_column(String(16), nullable=False, default="unknown")
    account_created_at: Mapped[datetime | None] = mapped_column(nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint("tenant_id", "external_id_hash", name="actor_tenant_extid"),
        CheckConstraint(
            "claimed_age_band in ('under_13','13_15','16_17','18_plus','unknown')",
            name="age_band_valid",
        ),
        CheckConstraint("char_length(external_id_hash) = 64", name="extid_hash_len"),
    )


class Conversation(Base):
    __tablename__ = "conversation"

    id: Mapped[UUID] = uuid_pk()
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True
    )
    participant_actor_ids: Mapped[list[Any]] = mapped_column(ARRAY(String(36)), nullable=False)
    started_at: Mapped[datetime] = mapped_column(nullable=False)
    last_message_at: Mapped[datetime] = mapped_column(nullable=False)
    channel_type: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))

    __table_args__ = (
        CheckConstraint(
            "channel_type in ('dm','group','public','voice_transcript')",
            name="channel_type_valid",
        ),
        CheckConstraint("last_message_at >= started_at", name="last_after_started"),
        Index(
            "ix_conversation_tenant_last_message",
            "tenant_id",
            "last_message_at",
        ),
    )


class Event(Base):
    __tablename__ = "event"

    id: Mapped[UUID] = uuid_pk()
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversation.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[UUID] = mapped_column(
        ForeignKey("actor.id", ondelete="CASCADE"), nullable=False
    )
    target_actor_ids: Mapped[list[Any]] = mapped_column(
        ARRAY(String(36)), nullable=False, server_default="{}"
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    content_features: Mapped[dict[str, Any]] = mapped_column(
        nullable=False, server_default=text("'{}'::jsonb")
    )
    processed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    score_delta: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    pattern_match_ids: Mapped[list[Any]] = mapped_column(
        ARRAY(String(36)), nullable=False, server_default="{}"
    )
    idempotency_key: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))

    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="event_tenant_idem"),
        CheckConstraint(
            "type in ('message','image','video','friend_request','gift',"
            "'profile_change','voice_clip','system')",
            name="event_type_valid",
        ),
        CheckConstraint("char_length(content_hash) = 64", name="content_hash_len"),
        Index("ix_event_actor_ts", "actor_id", "timestamp"),
        Index("ix_event_conversation_ts", "conversation_id", "timestamp"),
        Index("ix_event_tenant_ts", "tenant_id", "timestamp"),
    )


class SuspicionProfile(Base):
    __tablename__ = "suspicion_profile"

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), primary_key=True
    )
    actor_id: Mapped[UUID] = mapped_column(
        ForeignKey("actor.id", ondelete="CASCADE"), primary_key=True
    )
    current_score: Mapped[int] = mapped_column(Integer, nullable=False, server_default="5")
    tier: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    tier_entered_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
    last_updated: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
    last_decay_applied: Mapped[datetime] = mapped_column(
        nullable=False, server_default=text("now()")
    )
    escalation_markers: Mapped[list[Any]] = mapped_column(
        nullable=False, server_default=text("'[]'::jsonb")
    )
    network_signals: Mapped[dict[str, Any]] = mapped_column(
        nullable=False, server_default=text("'{}'::jsonb")
    )
    notes: Mapped[list[Any]] = mapped_column(nullable=False, server_default=text("'[]'::jsonb"))

    __table_args__ = (
        CheckConstraint("current_score between 0 and 100", name="score_bounds"),
        CheckConstraint("tier between 0 and 5", name="tier_bounds"),
        Index("ix_profile_tenant_tier", "tenant_id", "tier"),
        Index("ix_profile_tenant_score", "tenant_id", "current_score"),
    )


class ScoreHistory(Base):
    __tablename__ = "score_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[UUID] = mapped_column(
        ForeignKey("actor.id", ondelete="CASCADE"), nullable=False
    )
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_score: Mapped[int] = mapped_column(Integer, nullable=False)
    new_score: Mapped[int] = mapped_column(Integer, nullable=False)
    cause: Mapped[str] = mapped_column(String(200), nullable=False)
    event_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("event.id", ondelete="SET NULL"), nullable=True
    )
    pattern_match_id: Mapped[UUID | None] = mapped_column(nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))

    __table_args__ = (Index("ix_score_history_actor_ts", "tenant_id", "actor_id", "recorded_at"),)


class PatternMatch(Base):
    __tablename__ = "pattern_match"

    id: Mapped[UUID] = uuid_pk()
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[UUID] = mapped_column(
        ForeignKey("actor.id", ondelete="CASCADE"), nullable=False
    )
    pattern_id: Mapped[str] = mapped_column(String(100), nullable=False)
    pattern_version: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[float] = mapped_column(nullable=False)
    event_ids: Mapped[list[Any]] = mapped_column(ARRAY(String(36)), nullable=False)
    matched_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False)
    stage: Mapped[str | None] = mapped_column(String(40), nullable=True)

    __table_args__ = (
        CheckConstraint("confidence between 0.0 and 1.0", name="confidence_bounds"),
        Index("ix_pm_tenant_actor_ts", "tenant_id", "actor_id", "matched_at"),
        Index("ix_pm_pattern", "pattern_id"),
    )


class RelationshipEdge(Base):
    __tablename__ = "relationship_edge"

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), primary_key=True
    )
    actor_a: Mapped[UUID] = mapped_column(
        ForeignKey("actor.id", ondelete="CASCADE"), primary_key=True
    )
    actor_b: Mapped[UUID] = mapped_column(
        ForeignKey("actor.id", ondelete="CASCADE"), primary_key=True
    )
    interaction_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    first_interaction: Mapped[datetime] = mapped_column(nullable=False)
    last_interaction: Mapped[datetime] = mapped_column(nullable=False)
    signals: Mapped[dict[str, Any]] = mapped_column(
        nullable=False, server_default=text("'{}'::jsonb")
    )

    __table_args__ = (
        CheckConstraint("actor_a < actor_b", name="canonical_edge_order"),
        Index("ix_edge_tenant_a", "tenant_id", "actor_a"),
        Index("ix_edge_tenant_b", "tenant_id", "actor_b"),
    )


class ResponseAction(Base):
    __tablename__ = "response_action"

    id: Mapped[UUID] = uuid_pk()
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[UUID] = mapped_column(
        ForeignKey("actor.id", ondelete="CASCADE"), nullable=False
    )
    tier: Mapped[int] = mapped_column(Integer, nullable=False)
    actions: Mapped[list[Any]] = mapped_column(nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
    triggered_by_event_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("event.id", ondelete="SET NULL"), nullable=True
    )
    reasoning: Mapped[dict[str, Any]] = mapped_column(
        nullable=False, server_default=text("'{}'::jsonb")
    )
    delivered_to_platform_at: Mapped[datetime | None] = mapped_column(nullable=True)
    acknowledged_by_platform_at: Mapped[datetime | None] = mapped_column(nullable=True)

    __table_args__ = (
        CheckConstraint("tier between 0 and 5", name="response_tier_bounds"),
        Index("ix_response_tenant_actor_ts", "tenant_id", "actor_id", "triggered_at"),
    )


class AuditLogEntry(Base):
    __tablename__ = "audit_log_entry"

    id: Mapped[UUID] = uuid_pk()
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("actor.id", ondelete="SET NULL"), nullable=True
    )
    sequence: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(
        nullable=False, server_default=text("'{}'::jsonb")
    )
    timestamp: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
    previous_entry_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    entry_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "sequence", name="audit_seq_per_tenant"),
        CheckConstraint("char_length(entry_hash) = 64", name="entry_hash_len"),
        CheckConstraint("char_length(previous_entry_hash) = 64", name="prev_hash_len"),
        Index("ix_audit_tenant_ts", "tenant_id", "timestamp"),
    )


class TenantActionConfig(Base):
    __tablename__ = "tenant_action_config"

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), primary_key=True
    )
    mode: Mapped[str] = mapped_column(String(20), nullable=False, server_default="advisory")
    action_overrides: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb")
    )
    webhook_secret_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        CheckConstraint("mode in ('advisory','auto_enforce')", name="action_mode_valid"),
    )


class Reasoning(Base):
    __tablename__ = "reasoning"

    id: Mapped[UUID] = uuid_pk()
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[UUID] = mapped_column(
        ForeignKey("actor.id", ondelete="CASCADE"), nullable=False
    )
    event_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("event.id", ondelete="SET NULL"), nullable=True
    )
    reasoning_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        Index("ix_reasoning_tenant_actor_created", "tenant_id", "actor_id", "created_at"),
        Index("ix_reasoning_tenant_event", "tenant_id", "event_id"),
    )


class PatternDefinition(Base):
    __tablename__ = "pattern_definition"

    pattern_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    version: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    default_confidence: Mapped[float] = mapped_column(nullable=False)
    stage: Mapped[str | None] = mapped_column(String(40), nullable=True)
    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", nullable=False, server_default=text("'{}'::jsonb")
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
    retired_at: Mapped[datetime | None] = mapped_column(nullable=True)

    __table_args__ = (
        CheckConstraint("mode in ('rule','llm','hybrid')", name="pattern_mode_valid"),
        CheckConstraint("default_confidence between 0.0 and 1.0", name="pattern_conf_bounds"),
    )


class DashboardUser(Base):
    __tablename__ = "dashboard_user"

    id: Mapped[UUID] = uuid_pk()
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_dashboard_user_tenant_id_email"),
        CheckConstraint(
            "role in ('admin','mod','viewer','auditor','researcher')",
            name="ck_dashboard_user_role_valid",
        ),
    )


class HoneypotEvidencePackage(Base):
    __tablename__ = "honeypot_evidence_package"

    id: Mapped[UUID] = uuid_pk()
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[UUID] = mapped_column(
        ForeignKey("actor.id", ondelete="CASCADE"), nullable=False
    )
    persona_id: Mapped[str] = mapped_column(String(64), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    json_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        CheckConstraint("char_length(content_hash) = 64", name="ck_honeypot_content_hash_len"),
        Index("ix_honeypot_evidence_tenant_created", "tenant_id", "created_at"),
    )


class FederationTenantSecret(Base):
    __tablename__ = "federation_tenant_secret"

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), primary_key=True
    )
    hmac_secret: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    actor_pepper: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class FederationPublisher(Base):
    __tablename__ = "federation_publisher"

    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), primary_key=True
    )
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    jurisdictions: Mapped[list[Any]] = mapped_column(
        ARRAY(Text), nullable=False, server_default="{}"
    )
    reputation: Mapped[int] = mapped_column(Integer, nullable=False, server_default="50")
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    hmac_secret: Mapped[bytes] = mapped_column(BYTEA, nullable=False)


class FederationSignal(Base):
    __tablename__ = "federation_signal"

    id: Mapped[UUID] = uuid_pk()
    publisher_tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("federation_publisher.tenant_id", ondelete="CASCADE"), nullable=False
    )
    fingerprint: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    signal_kinds: Mapped[list[Any]] = mapped_column(ARRAY(Text), nullable=False)
    flagged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    commit: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class FederationReputationEvent(Base):
    __tablename__ = "federation_reputation_event"

    id: Mapped[UUID] = uuid_pk()
    publisher_tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("federation_publisher.tenant_id", ondelete="CASCADE"), nullable=False
    )
    reporter_tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )


class SyntheticRun(Base):
    __tablename__ = "synthetic_run"

    id: Mapped[UUID] = uuid_pk()
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    requested_by_user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("dashboard_user.id", ondelete="SET NULL"), nullable=True
    )
    seed: Mapped[int] = mapped_column(BigInteger, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    axes: Mapped[dict[str, Any]] = mapped_column(nullable=False)
    stage_mix: Mapped[dict[str, Any]] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))

    __table_args__ = (
        CheckConstraint(
            "status in ('pending','running','completed','failed')",
            name="ck_synthetic_run_status_valid",
        ),
    )


class SyntheticConversation(Base):
    __tablename__ = "synthetic_conversation"

    id: Mapped[UUID] = uuid_pk()
    run_id: Mapped[UUID] = mapped_column(
        ForeignKey("synthetic_run.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    stage: Mapped[str] = mapped_column(String(40), nullable=False)
    demographics: Mapped[dict[str, Any] | None] = mapped_column(nullable=True)
    platform: Mapped[str | None] = mapped_column(String(40), nullable=True)
    communication_style: Mapped[str | None] = mapped_column(String(40), nullable=True)
    turns: Mapped[list[Any]] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))

    __table_args__ = (Index("ix_synthetic_conversation_tenant_run", "tenant_id", "run_id"),)


class BugReport(Base):
    __tablename__ = "bug_report"

    id: Mapped[UUID] = uuid_pk()
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reporter_email: Mapped[str] = mapped_column(String(320), nullable=False)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="new")
    received_at: Mapped[datetime] = mapped_column(nullable=False, server_default=text("now()"))
    resolved_at: Mapped[datetime | None] = mapped_column(nullable=True)

    __table_args__ = (
        CheckConstraint(
            "severity in ('low','medium','high','critical')",
            name="ck_bug_report_severity_valid",
        ),
        CheckConstraint(
            "status in ('new','triaging','accepted','rejected','resolved')",
            name="ck_bug_report_status_valid",
        ),
        Index("ix_bug_report_tenant_received", "tenant_id", "received_at"),
    )


class HoneypotActivationLog(Base):
    __tablename__ = "honeypot_activation_log"

    id: Mapped[UUID] = uuid_pk()
    tenant_id: Mapped[UUID] = mapped_column(
        ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False
    )
    actor_id: Mapped[UUID] = mapped_column(
        ForeignKey("actor.id", ondelete="CASCADE"), nullable=False
    )
    persona_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    activated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    decision: Mapped[str] = mapped_column(String(16), nullable=False)
    decision_reasons: Mapped[list[Any]] = mapped_column(
        ARRAY(String(64)), nullable=False, server_default="{}"
    )
    evidence_package_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("honeypot_evidence_package.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    __table_args__ = (
        CheckConstraint("decision in ('allow','deny')", name="ck_honeypot_decision_valid"),
        Index(
            "ix_honeypot_log_tenant_actor_activated",
            "tenant_id",
            "actor_id",
            "activated_at",
        ),
    )
