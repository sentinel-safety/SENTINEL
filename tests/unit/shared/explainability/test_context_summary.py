# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.explainability.context_summary import build_context_summary
from shared.graph.views import ContactGraphView
from shared.memory.repository import ActorMemoryView

pytestmark = pytest.mark.unit


def test_empty_inputs_return_empty_string() -> None:
    assert build_context_summary(memory=None, contact_graph=None, actor_age_days=None) == ""


def test_graph_only_summary() -> None:
    graph = ContactGraphView(
        distinct_contacts_total=12,
        distinct_minor_contacts_window=7,
        contact_velocity_per_day=0.5,
        age_band_distribution={"13_15": 7},
        lookback_days=14,
    )
    out = build_context_summary(memory=None, contact_graph=graph, actor_age_days=None)
    assert "7 distinct minor" in out
    assert "14" in out


def test_account_age_summary() -> None:
    out = build_context_summary(memory=None, contact_graph=None, actor_age_days=18)
    assert "18" in out
    assert "created" in out.lower()


def test_combined_summary_uses_sentences() -> None:
    graph = ContactGraphView(
        distinct_contacts_total=12,
        distinct_minor_contacts_window=7,
        contact_velocity_per_day=0.5,
        age_band_distribution={"13_15": 7},
        lookback_days=14,
    )
    mem = ActorMemoryView(
        distinct_conversations_last_window=4,
        distinct_minor_targets_last_window=3,
        pattern_counts_by_kind={},
        stages_observed=(),
        first_contact_at=None,
        most_recent_contact_at=None,
        total_events_last_window=10,
    )
    out = build_context_summary(memory=mem, contact_graph=graph, actor_age_days=18)
    assert "7 distinct minor" in out
    assert "3" in out
    assert "18" in out
    assert out.endswith(".")
