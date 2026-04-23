# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.config import Settings

pytestmark = pytest.mark.unit


def test_memory_base_url_default() -> None:
    settings = Settings()
    assert settings.memory_base_url == "http://127.0.0.1:8001"


def test_memory_lookback_days_default() -> None:
    settings = Settings()
    assert settings.memory_lookback_days == 21


def test_memory_settings_overridable_via_constructor() -> None:
    settings = Settings(memory_base_url="http://memory", memory_lookback_days=14)
    assert settings.memory_base_url == "http://memory"
    assert settings.memory_lookback_days == 14
