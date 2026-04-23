# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.config.settings import Settings

pytestmark = pytest.mark.unit


def test_federation_enabled_globally_default() -> None:
    assert Settings().federation_enabled_globally is False


def test_federation_signals_stream_default() -> None:
    assert Settings().federation_signals_stream == "federation:signals"


def test_federation_qdrant_collection_default() -> None:
    assert Settings().federation_qdrant_collection == "federated_fingerprints"


def test_federation_publish_tier_threshold_default() -> None:
    assert Settings().federation_publish_tier_threshold == "restrict"


def test_federation_advisory_delta_default() -> None:
    assert Settings().federation_advisory_delta == 10


def test_federation_low_reputation_delta_default() -> None:
    assert Settings().federation_low_reputation_delta == 3


def test_federation_low_reputation_threshold_default() -> None:
    assert Settings().federation_low_reputation_threshold == 30


def test_federation_base_url_default() -> None:
    assert Settings().federation_base_url == "http://127.0.0.1:8011"


def test_federation_consumer_block_ms_default() -> None:
    assert Settings().federation_consumer_block_ms == 2000
