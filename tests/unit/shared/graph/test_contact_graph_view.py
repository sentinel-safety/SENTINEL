# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.graph.views import ContactGraphView

pytestmark = pytest.mark.unit


def test_contact_graph_view_defaults() -> None:
    view = ContactGraphView(
        distinct_contacts_total=0,
        distinct_minor_contacts_window=0,
        contact_velocity_per_day=0.0,
        age_band_distribution={},
        lookback_days=7,
    )
    assert view.distinct_minor_contacts_window == 0


def test_contact_graph_view_rejects_negative_counts() -> None:
    with pytest.raises(ValueError):
        ContactGraphView(
            distinct_contacts_total=-1,
            distinct_minor_contacts_window=0,
            contact_velocity_per_day=0.0,
            age_band_distribution={},
            lookback_days=7,
        )


def test_contact_graph_view_frozen() -> None:
    view = ContactGraphView(
        distinct_contacts_total=3,
        distinct_minor_contacts_window=2,
        contact_velocity_per_day=1.5,
        age_band_distribution={"under_13": 2, "13_15": 1},
        lookback_days=7,
    )
    with pytest.raises(ValueError):
        view.distinct_contacts_total = 5  # type: ignore[misc]
