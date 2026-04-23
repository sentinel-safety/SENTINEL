# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from services.patterns.app.library.behavioral_fingerprint_match import (
    BehavioralFingerprintMatchPattern,
)
from services.patterns.app.library.cross_session_escalation import (
    CrossSessionEscalationPattern,
)
from services.patterns.app.library.multi_minor_contact import MultiMinorContactPattern
from services.patterns.app.library.suspicious_cluster_membership import (
    SuspiciousClusterMembershipPattern,
)
from shared.contracts.preprocess import ExtractedFeatures
from shared.explainability.evidence_templates import render_evidence
from shared.fingerprint.repository import FingerprintNeighbor
from shared.graph.views import ContactGraphView
from shared.memory.repository import ActorMemoryView
from shared.patterns.protocol import SyncPatternContext
from shared.schemas.enums import EventType
from shared.schemas.event import Event

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


def _ctx(
    *,
    contact_graph: ContactGraphView | None = None,
    memory: ActorMemoryView | None = None,
    neighbors: tuple[FingerprintNeighbor, ...] = (),
) -> SyncPatternContext:
    event = Event(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        target_actor_ids=(uuid.uuid4(),),
        timestamp=datetime.now(UTC),
        type=EventType.MESSAGE,
        content_hash="a" * 64,
    )
    features = ExtractedFeatures(
        normalized_content="hello",
        language="en",
        token_count=1,
        contains_url=False,
        contains_contact_request=False,
        minor_recipient=True,
        late_night_local=False,
    )
    return SyncPatternContext(
        event=event,
        features=features,
        actor_memory=memory,
        contact_graph=contact_graph,
        fingerprint_neighbors=neighbors,
    )


async def test_multi_minor_variables() -> None:
    graph = ContactGraphView(
        distinct_contacts_total=20,
        distinct_minor_contacts_window=5,
        contact_velocity_per_day=0.4,
        age_band_distribution={"13_15": 5},
        lookback_days=7,
    )
    matches = await MultiMinorContactPattern().detect_sync(_ctx(contact_graph=graph))
    out = render_evidence(
        pattern_name="multi_minor_contact",
        variables=dict(matches[0].template_variables),
    )
    assert "5" in out
    assert "7" in out


async def test_cross_session_escalation_variables() -> None:
    mem = ActorMemoryView(
        distinct_conversations_last_window=4,
        distinct_minor_targets_last_window=3,
        pattern_counts_by_kind={},
        stages_observed=(),
        first_contact_at=None,
        most_recent_contact_at=None,
        total_events_last_window=10,
    )
    matches = await CrossSessionEscalationPattern().detect_sync(_ctx(memory=mem))
    out = render_evidence(
        pattern_name="cross_session_escalation",
        variables=dict(matches[0].template_variables),
    )
    assert "4" in out
    assert "3" in out


async def test_behavioral_fingerprint_variables() -> None:
    tenant_id = uuid.uuid4()
    neighbor = FingerprintNeighbor(
        tenant_id=tenant_id, actor_id=uuid.uuid4(), score=0.92, flagged=True
    )
    matches = await BehavioralFingerprintMatchPattern().detect_sync(_ctx(neighbors=(neighbor,)))
    out = render_evidence(
        pattern_name="behavioral_fingerprint_match",
        variables=dict(matches[0].template_variables),
    )
    assert "0.92" in out or "0.9" in out


async def test_cluster_membership_variables() -> None:
    tenant_id = uuid.uuid4()
    neighbors = tuple(
        FingerprintNeighbor(tenant_id=tenant_id, actor_id=uuid.uuid4(), score=0.9, flagged=True)
        for _ in range(3)
    )
    matches = await SuspiciousClusterMembershipPattern().detect_sync(_ctx(neighbors=neighbors))
    out = render_evidence(
        pattern_name="suspicious_cluster_membership",
        variables=dict(matches[0].template_variables),
    )
    assert "3" in out
