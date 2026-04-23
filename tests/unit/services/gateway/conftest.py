# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from services.gateway.app.main import create_app
from shared.config import Settings
from shared.observability import reset_observability


@pytest.fixture
def test_settings() -> Settings:
    return Settings(env="test", log_level="INFO", service_name="sentinel-gateway")


@pytest.fixture
def client(test_settings: Settings) -> Iterator[TestClient]:
    app = create_app(test_settings)
    with TestClient(app) as c:
        yield c
    reset_observability()
