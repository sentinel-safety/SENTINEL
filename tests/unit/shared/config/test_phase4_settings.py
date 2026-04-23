# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.config.settings import Settings

pytestmark = pytest.mark.unit


def test_phase4_defaults() -> None:
    s = Settings()
    assert s.qdrant_fingerprint_collection == "actor_fingerprints"
    assert s.fingerprint_vector_dim == 16
    assert s.graph_lookback_days == 7
    assert s.graph_base_url == "http://127.0.0.1:8006"
    assert 0.0 < s.fingerprint_similarity_threshold <= 1.0
    assert s.cluster_min_flagged_neighbors >= 1
    assert s.fingerprint_search_top_k >= 5
