# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.config.settings import Settings

pytestmark = pytest.mark.unit


def test_synthetic_base_url_default() -> None:
    assert Settings().synthetic_base_url == "http://127.0.0.1:8012"


def test_synthetic_researcher_token_ttl_minutes_default() -> None:
    assert Settings().synthetic_researcher_token_ttl_minutes == 60


def test_synthetic_default_seed_default() -> None:
    assert Settings().synthetic_default_seed == 424242
