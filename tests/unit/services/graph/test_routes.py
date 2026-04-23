# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from services.graph.app.main import create_app
from shared.config import Settings

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


async def test_routes_registered() -> None:
    app = create_app(Settings(env="test"))
    paths = {r.path for r in app.routes if hasattr(r, "path")}
    assert "/internal/contact-graph" in paths
    assert "/internal/fingerprint/upsert" in paths
    assert "/internal/fingerprint/similar" in paths


async def test_healthz_still_there() -> None:
    app = create_app(Settings(env="test"))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/healthz")
    assert resp.status_code == 200
