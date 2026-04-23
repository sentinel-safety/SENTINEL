# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest
from sqlalchemy import UniqueConstraint

from shared.db import Base

pytestmark = pytest.mark.unit


def test_all_expected_tables_registered() -> None:
    names = set(Base.metadata.tables.keys())
    assert names == {
        "tenant",
        "api_key",
        "webhook_endpoint",
        "actor",
        "conversation",
        "event",
        "suspicion_profile",
        "score_history",
        "pattern_match",
        "relationship_edge",
        "response_action",
        "audit_log_entry",
        "pattern_definition",
        "tenant_action_config",
        "reasoning",
        "dashboard_user",
        "honeypot_activation_log",
        "honeypot_evidence_package",
        "federation_tenant_secret",
        "federation_publisher",
        "federation_signal",
        "federation_reputation_event",
        "synthetic_run",
        "synthetic_conversation",
        "bug_report",
    }


def test_actor_has_tenant_extid_unique_constraint() -> None:
    actor = Base.metadata.tables["actor"]
    unique_cols = {
        tuple(c.name for c in uc.columns)
        for uc in actor.constraints
        if isinstance(uc, UniqueConstraint)
    }
    assert ("tenant_id", "external_id_hash") in unique_cols


def test_suspicion_profile_is_composite_pk() -> None:
    profile = Base.metadata.tables["suspicion_profile"]
    pk_cols = [c.name for c in profile.primary_key.columns]
    assert pk_cols == ["tenant_id", "actor_id"]


def test_relationship_edge_canonical_order_constraint_present() -> None:
    edge = Base.metadata.tables["relationship_edge"]
    check_sqls = {str(c.sqltext) for c in edge.constraints if hasattr(c, "sqltext")}
    assert any("actor_a < actor_b" in s for s in check_sqls)


def test_audit_log_entry_has_sequence_unique_per_tenant() -> None:
    audit = Base.metadata.tables["audit_log_entry"]
    unique_cols = {
        tuple(c.name for c in uc.columns)
        for uc in audit.constraints
        if isinstance(uc, UniqueConstraint)
    }
    assert ("tenant_id", "sequence") in unique_cols


def test_event_has_idempotency_key_unique_per_tenant() -> None:
    event = Base.metadata.tables["event"]
    unique_cols = {
        tuple(c.name for c in uc.columns)
        for uc in event.constraints
        if isinstance(uc, UniqueConstraint)
    }
    assert ("tenant_id", "idempotency_key") in unique_cols


def test_all_tenant_scoped_tables_cascade_delete() -> None:
    tenant_scoped = {
        "api_key",
        "webhook_endpoint",
        "actor",
        "conversation",
        "event",
        "suspicion_profile",
        "score_history",
        "pattern_match",
        "relationship_edge",
        "response_action",
        "audit_log_entry",
        "tenant_action_config",
        "reasoning",
        "dashboard_user",
        "honeypot_activation_log",
        "honeypot_evidence_package",
        "federation_tenant_secret",
        "federation_publisher",
        "federation_reputation_event",
        "synthetic_run",
        "synthetic_conversation",
        "bug_report",
    }
    for name in tenant_scoped:
        table = Base.metadata.tables[name]
        fk_to_tenant = next(
            (fk for fk in table.foreign_keys if fk.column.table.name == "tenant"),
            None,
        )
        assert fk_to_tenant is not None, f"{name} missing fk to tenant"
        assert fk_to_tenant.ondelete == "CASCADE", f"{name} tenant fk must cascade delete"
