# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import uuid4

import pytest

from shared.contracts.graph import (
    ContactGraphLookupRequest,
    ContactGraphLookupResponse,
    FingerprintSimilarRequest,
    FingerprintSimilarResponse,
    FingerprintUpsertRequest,
)
from shared.fingerprint.repository import FingerprintNeighbor
from shared.graph.views import ContactGraphView

pytestmark = pytest.mark.unit


def test_contact_graph_lookup_round_trip() -> None:
    req = ContactGraphLookupRequest(tenant_id=uuid4(), actor_id=uuid4(), lookback_days=7)
    view = ContactGraphView(
        distinct_contacts_total=3,
        distinct_minor_contacts_window=2,
        contact_velocity_per_day=0.5,
        age_band_distribution={"under_13": 2},
        lookback_days=7,
    )
    resp = ContactGraphLookupResponse(view=view)
    assert resp.view.distinct_minor_contacts_window == 2
    assert req.lookback_days == 7


def test_fingerprint_upsert_request_validates_dim() -> None:
    with pytest.raises(ValueError):
        FingerprintUpsertRequest(
            tenant_id=uuid4(),
            actor_id=uuid4(),
            vector=(0.1,) * 4,
            flagged=False,
        )


def test_fingerprint_similar_round_trip() -> None:
    tenant = uuid4()
    actor = uuid4()
    req = FingerprintSimilarRequest(tenant_id=tenant, actor_id=actor, vector=(0.0,) * 16, top_k=5)
    resp = FingerprintSimilarResponse(
        neighbors=(
            FingerprintNeighbor(tenant_id=tenant, actor_id=uuid4(), score=0.9, flagged=True),
        )
    )
    assert req.top_k == 5
    assert len(resp.neighbors) == 1
