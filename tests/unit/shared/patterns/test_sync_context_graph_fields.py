# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from shared.contracts.preprocess import ExtractedFeatures
from shared.fingerprint.repository import FingerprintNeighbor
from shared.graph.views import ContactGraphView
from shared.patterns import SyncPatternContext
from shared.schemas.enums import EventType
from shared.schemas.event import Event

pytestmark = pytest.mark.unit


def _event() -> Event:
    return Event(
        id=uuid4(),
        tenant_id=uuid4(),
        conversation_id=uuid4(),
        actor_id=uuid4(),
        timestamp=datetime.now(UTC),
        type=EventType.MESSAGE,
        content_hash="a" * 64,
    )


def _features() -> ExtractedFeatures:
    return ExtractedFeatures(
        normalized_content="hi",
        language="en",
        token_count=1,
        contains_url=False,
        contains_contact_request=False,
        minor_recipient=True,
        late_night_local=False,
    )


def test_defaults_are_none_and_empty() -> None:
    ctx = SyncPatternContext(event=_event(), features=_features())
    assert ctx.contact_graph is None
    assert ctx.fingerprint_neighbors == ()


def test_accepts_graph_and_neighbors() -> None:
    tenant = uuid4()
    view = ContactGraphView(
        distinct_contacts_total=3,
        distinct_minor_contacts_window=2,
        contact_velocity_per_day=1.0,
        age_band_distribution={"under_13": 2},
        lookback_days=7,
    )
    neighbor = FingerprintNeighbor(tenant_id=tenant, actor_id=uuid4(), score=0.95, flagged=True)
    ctx = SyncPatternContext(
        event=_event(),
        features=_features(),
        contact_graph=view,
        fingerprint_neighbors=(neighbor,),
    )
    assert ctx.contact_graph is view
    assert ctx.fingerprint_neighbors == (neighbor,)
