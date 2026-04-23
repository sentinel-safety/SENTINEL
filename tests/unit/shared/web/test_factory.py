# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from shared.config import Settings
from shared.observability import reset_observability
from shared.web import create_service_app

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _reset_observability() -> Iterator[None]:
    yield
    reset_observability()


def test_factory_returns_fastapi_app() -> None:
    app = create_service_app(
        title="S",
        description="d",
        service_name="svc",
        settings=Settings(env="test"),
    )
    assert isinstance(app, FastAPI)
    assert app.title == "S"


def test_factory_overrides_service_name() -> None:
    app = create_service_app(
        title="S",
        description="d",
        service_name="svc-name",
        settings=Settings(env="test", service_name="original"),
    )
    assert app.state.settings.service_name == "svc-name"


def test_factory_mounts_meta_endpoints() -> None:
    app = create_service_app(
        title="S", description="d", service_name="svc", settings=Settings(env="test")
    )
    with TestClient(app) as client:
        assert client.get("/healthz").json() == {"status": "ok"}
        assert client.get("/readyz").json() == {"status": "ready"}


def test_factory_mounts_extra_routers() -> None:
    extra = APIRouter()

    @extra.get("/custom")
    def custom() -> dict[str, str]:
        return {"ok": "yes"}

    app = create_service_app(
        title="S",
        description="d",
        service_name="svc",
        settings=Settings(env="test"),
        routers=[extra],
    )
    with TestClient(app) as client:
        assert client.get("/custom").json() == {"ok": "yes"}
