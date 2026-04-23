# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.config.settings import Settings

pytestmark = pytest.mark.unit


def test_reasoning_retention_days_default() -> None:
    assert Settings().reasoning_retention_days == 90


def test_reasoning_retention_days_has_bounds() -> None:
    with pytest.raises(ValueError):
        Settings(reasoning_retention_days=0)
    with pytest.raises(ValueError):
        Settings(reasoning_retention_days=4000)
