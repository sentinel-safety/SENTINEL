"""initial schema"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pattern_definition",
        sa.Column("pattern_id", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column("default_confidence", sa.Float(), nullable=False),
        sa.Column("stage", sa.String(length=40), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("retired_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "mode in ('rule','llm','hybrid')", name=op.f("ck_pattern_definition_pattern_mode_valid")
        ),
        sa.CheckConstraint(
            "default_confidence between 0.0 and 1.0",
            name=op.f("ck_pattern_definition_pattern_conf_bounds"),
        ),
        sa.PrimaryKeyConstraint("pattern_id", "version", name=op.f("pk_pattern_definition")),
    )
    op.create_table(
        "tenant",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("tier", sa.String(length=20), nullable=False),
        sa.Column(
            "compliance_jurisdictions",
            postgresql.ARRAY(sa.String(length=16)),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("data_retention_days", sa.Integer(), nullable=False),
        sa.Column(
            "feature_flags",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tenant")),
    )
    op.create_table(
        "actor",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("external_id_hash", sa.String(length=64), nullable=False),
        sa.Column("claimed_age_band", sa.String(length=16), nullable=False),
        sa.Column("account_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "claimed_age_band in ('under_13','13_15','16_17','18_plus','unknown')",
            name=op.f("ck_actor_age_band_valid"),
        ),
        sa.CheckConstraint(
            "char_length(external_id_hash) = 64", name=op.f("ck_actor_extid_hash_len")
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name=op.f("fk_actor_tenant_id_tenant"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_actor")),
        sa.UniqueConstraint("tenant_id", "external_id_hash", name="actor_tenant_extid"),
    )
    op.create_table(
        "api_key",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("key_hash", sa.String(length=128), nullable=False),
        sa.Column("key_prefix", sa.String(length=16), nullable=False),
        sa.Column("scope", sa.String(length=16), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "scope in ('read','write','admin')", name=op.f("ck_api_key_scope_valid")
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_api_key_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_api_key")),
        sa.UniqueConstraint("key_hash", name=op.f("uq_api_key_key_hash")),
    )
    op.create_index(op.f("ix_api_key_tenant_id"), "api_key", ["tenant_id"], unique=False)
    op.create_table(
        "conversation",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("participant_actor_ids", postgresql.ARRAY(sa.String(length=36)), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("channel_type", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "channel_type in ('dm','group','public','voice_transcript')",
            name=op.f("ck_conversation_channel_type_valid"),
        ),
        sa.CheckConstraint(
            "last_message_at >= started_at", name=op.f("ck_conversation_last_after_started")
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_conversation_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_conversation")),
    )
    op.create_index(op.f("ix_conversation_tenant_id"), "conversation", ["tenant_id"], unique=False)
    op.create_index(
        "ix_conversation_tenant_last_message",
        "conversation",
        ["tenant_id", "last_message_at"],
        unique=False,
    )
    op.create_table(
        "webhook_endpoint",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("url", sa.String(length=2000), nullable=False),
        sa.Column("secret_hash", sa.String(length=128), nullable=False),
        sa.Column(
            "subscribed_topics",
            postgresql.ARRAY(sa.String(length=64)),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_webhook_endpoint_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_webhook_endpoint")),
    )
    op.create_index(
        op.f("ix_webhook_endpoint_tenant_id"), "webhook_endpoint", ["tenant_id"], unique=False
    )
    op.create_table(
        "audit_log_entry",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=True),
        sa.Column("sequence", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column(
            "details",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("previous_entry_hash", sa.String(length=64), nullable=False),
        sa.Column("entry_hash", sa.String(length=64), nullable=False),
        sa.CheckConstraint(
            "char_length(entry_hash) = 64", name=op.f("ck_audit_log_entry_entry_hash_len")
        ),
        sa.CheckConstraint(
            "char_length(previous_entry_hash) = 64", name=op.f("ck_audit_log_entry_prev_hash_len")
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["actor.id"],
            name=op.f("fk_audit_log_entry_actor_id_actor"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_audit_log_entry_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_log_entry")),
        sa.UniqueConstraint("entry_hash", name=op.f("uq_audit_log_entry_entry_hash")),
        sa.UniqueConstraint("tenant_id", "sequence", name="audit_seq_per_tenant"),
    )
    op.create_index(
        "ix_audit_tenant_ts", "audit_log_entry", ["tenant_id", "timestamp"], unique=False
    )
    op.create_table(
        "event",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column(
            "target_actor_ids",
            postgresql.ARRAY(sa.String(length=36)),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "content_features",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score_delta", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "pattern_match_ids",
            postgresql.ARRAY(sa.String(length=36)),
            server_default="{}",
            nullable=False,
        ),
        sa.Column("idempotency_key", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "type in ('message','image','video','friend_request','gift','profile_change','voice_clip','system')",
            name=op.f("ck_event_event_type_valid"),
        ),
        sa.CheckConstraint(
            "char_length(content_hash) = 64", name=op.f("ck_event_content_hash_len")
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"], ["actor.id"], name=op.f("fk_event_actor_id_actor"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversation.id"],
            name=op.f("fk_event_conversation_id_conversation"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant.id"], name=op.f("fk_event_tenant_id_tenant"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event")),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="event_tenant_idem"),
    )
    op.create_index("ix_event_actor_ts", "event", ["actor_id", "timestamp"], unique=False)
    op.create_index(
        "ix_event_conversation_ts", "event", ["conversation_id", "timestamp"], unique=False
    )
    op.create_index("ix_event_tenant_ts", "event", ["tenant_id", "timestamp"], unique=False)
    op.create_table(
        "pattern_match",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("pattern_id", sa.String(length=100), nullable=False),
        sa.Column("pattern_version", sa.String(length=32), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("event_ids", postgresql.ARRAY(sa.String(length=36)), nullable=False),
        sa.Column(
            "matched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("evidence_summary", sa.Text(), nullable=False),
        sa.Column("stage", sa.String(length=40), nullable=True),
        sa.CheckConstraint(
            "confidence between 0.0 and 1.0", name=op.f("ck_pattern_match_confidence_bounds")
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["actor.id"],
            name=op.f("fk_pattern_match_actor_id_actor"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_pattern_match_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_pattern_match")),
    )
    op.create_index("ix_pm_pattern", "pattern_match", ["pattern_id"], unique=False)
    op.create_index(
        "ix_pm_tenant_actor_ts",
        "pattern_match",
        ["tenant_id", "actor_id", "matched_at"],
        unique=False,
    )
    op.create_table(
        "relationship_edge",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("actor_a", sa.UUID(), nullable=False),
        sa.Column("actor_b", sa.UUID(), nullable=False),
        sa.Column("interaction_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("first_interaction", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_interaction", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "signals",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "actor_a < actor_b", name=op.f("ck_relationship_edge_canonical_edge_order")
        ),
        sa.ForeignKeyConstraint(
            ["actor_a"],
            ["actor.id"],
            name=op.f("fk_relationship_edge_actor_a_actor"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["actor_b"],
            ["actor.id"],
            name=op.f("fk_relationship_edge_actor_b_actor"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_relationship_edge_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "tenant_id", "actor_a", "actor_b", name=op.f("pk_relationship_edge")
        ),
    )
    op.create_index("ix_edge_tenant_a", "relationship_edge", ["tenant_id", "actor_a"], unique=False)
    op.create_index("ix_edge_tenant_b", "relationship_edge", ["tenant_id", "actor_b"], unique=False)
    op.create_table(
        "suspicion_profile",
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("current_score", sa.Integer(), server_default="5", nullable=False),
        sa.Column("tier", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "tier_entered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_updated",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_decay_applied",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "escalation_markers",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "network_signals",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "notes",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "current_score between 0 and 100", name=op.f("ck_suspicion_profile_score_bounds")
        ),
        sa.CheckConstraint("tier between 0 and 5", name=op.f("ck_suspicion_profile_tier_bounds")),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["actor.id"],
            name=op.f("fk_suspicion_profile_actor_id_actor"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_suspicion_profile_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("tenant_id", "actor_id", name=op.f("pk_suspicion_profile")),
    )
    op.create_index(
        "ix_profile_tenant_score", "suspicion_profile", ["tenant_id", "current_score"], unique=False
    )
    op.create_index(
        "ix_profile_tenant_tier", "suspicion_profile", ["tenant_id", "tier"], unique=False
    )
    op.create_table(
        "response_action",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("tier", sa.Integer(), nullable=False),
        sa.Column(
            "actions",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=False,
        ),
        sa.Column(
            "triggered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("triggered_by_event_id", sa.UUID(), nullable=True),
        sa.Column(
            "reasoning",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("delivered_to_platform_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("acknowledged_by_platform_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "tier between 0 and 5", name=op.f("ck_response_action_response_tier_bounds")
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["actor.id"],
            name=op.f("fk_response_action_actor_id_actor"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_response_action_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["triggered_by_event_id"],
            ["event.id"],
            name=op.f("fk_response_action_triggered_by_event_id_event"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_response_action")),
    )
    op.create_index(
        "ix_response_tenant_actor_ts",
        "response_action",
        ["tenant_id", "actor_id", "triggered_at"],
        unique=False,
    )
    op.create_table(
        "score_history",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("delta", sa.Integer(), nullable=False),
        sa.Column("previous_score", sa.Integer(), nullable=False),
        sa.Column("new_score", sa.Integer(), nullable=False),
        sa.Column("cause", sa.String(length=200), nullable=False),
        sa.Column("event_id", sa.UUID(), nullable=True),
        sa.Column("pattern_match_id", sa.UUID(), nullable=True),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["actor.id"],
            name=op.f("fk_score_history_actor_id_actor"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["event.id"],
            name=op.f("fk_score_history_event_id_event"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenant.id"],
            name=op.f("fk_score_history_tenant_id_tenant"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_score_history")),
    )
    op.create_index(
        "ix_score_history_actor_ts",
        "score_history",
        ["tenant_id", "actor_id", "recorded_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_score_history_actor_ts", table_name="score_history")
    op.drop_table("score_history")
    op.drop_index("ix_response_tenant_actor_ts", table_name="response_action")
    op.drop_table("response_action")
    op.drop_index("ix_profile_tenant_tier", table_name="suspicion_profile")
    op.drop_index("ix_profile_tenant_score", table_name="suspicion_profile")
    op.drop_table("suspicion_profile")
    op.drop_index("ix_edge_tenant_b", table_name="relationship_edge")
    op.drop_index("ix_edge_tenant_a", table_name="relationship_edge")
    op.drop_table("relationship_edge")
    op.drop_index("ix_pm_tenant_actor_ts", table_name="pattern_match")
    op.drop_index("ix_pm_pattern", table_name="pattern_match")
    op.drop_table("pattern_match")
    op.drop_index("ix_event_tenant_ts", table_name="event")
    op.drop_index("ix_event_conversation_ts", table_name="event")
    op.drop_index("ix_event_actor_ts", table_name="event")
    op.drop_table("event")
    op.drop_index("ix_audit_tenant_ts", table_name="audit_log_entry")
    op.drop_table("audit_log_entry")
    op.drop_index(op.f("ix_webhook_endpoint_tenant_id"), table_name="webhook_endpoint")
    op.drop_table("webhook_endpoint")
    op.drop_index("ix_conversation_tenant_last_message", table_name="conversation")
    op.drop_index(op.f("ix_conversation_tenant_id"), table_name="conversation")
    op.drop_table("conversation")
    op.drop_index(op.f("ix_api_key_tenant_id"), table_name="api_key")
    op.drop_table("api_key")
    op.drop_table("actor")
    op.drop_table("tenant")
    op.drop_table("pattern_definition")
