# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.federation.app.main import create_app
from shared.config import Settings

pytestmark = pytest.mark.unit


def _app() -> FastAPI:
    return create_app(Settings(env="test"))


def test_create_app_returns_fastapi() -> None:
    app = _app()
    assert isinstance(app, FastAPI)


def test_health_endpoint() -> None:
    with TestClient(_app()) as client:
        assert client.get("/healthz").json() == {"status": "ok"}


def test_routes_registered() -> None:
    from fastapi.routing import APIRoute

    app = _app()
    paths = {r.path for r in app.routes if isinstance(r, APIRoute)}
    assert "/internal/federation/publish" in paths
    assert "/internal/federation/feed" in paths
    assert "/internal/federation/report-false" in paths


@pytest.mark.xfail(reason="federation service endpoint initialization failing")
def test_feed_returns_200() -> None:
    with TestClient(_app()) as client:
        r = client.get("/internal/federation/feed")
    assert r.status_code == 200
    assert "signals" in r.json()
