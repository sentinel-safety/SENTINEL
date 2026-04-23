# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.config.settings import Settings

pytestmark = pytest.mark.unit


def test_dashboard_access_ttl_default() -> None:
    assert Settings().dashboard_access_token_ttl_minutes == 30


def test_dashboard_refresh_ttl_default() -> None:
    assert Settings().dashboard_refresh_token_ttl_days == 14


def test_dashboard_bff_base_url_default() -> None:
    assert Settings().dashboard_bff_base_url == "http://127.0.0.1:8009"


def test_dashboard_keys_default_none() -> None:
    s = Settings()
    assert s.dashboard_jwt_private_key_pem is None
    assert s.dashboard_jwt_public_key_pem is None


def test_ttl_bounds_enforced() -> None:
    with pytest.raises(ValueError):
        Settings(dashboard_access_token_ttl_minutes=0)
    with pytest.raises(ValueError):
        Settings(dashboard_refresh_token_ttl_days=0)
