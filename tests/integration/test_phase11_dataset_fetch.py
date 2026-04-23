# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

from services.synthetic_data.app.main import create_app
from tests.integration._phase7b_helpers import fast_settings, make_access_token, seed_tenant

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_SETTINGS = fast_settings()


def _researcher_headers(tenant_id: object) -> dict[str, str]:
    from uuid import UUID

    token = make_access_token(uuid4(), UUID(str(tenant_id)), role="researcher")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def _tables(clean_tables: None) -> None:
    pass


@pytest.mark.usefixtures("_tables")
async def test_fetch_nonexistent_run_returns_404(admin_engine: AsyncEngine) -> None:
    tenant_id = uuid4()
    await seed_tenant(admin_engine, str(tenant_id))

    app = create_app(_SETTINGS)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(
            f"/internal/synthetic/datasets/{uuid4()}",
            headers=_researcher_headers(tenant_id),
        )

    assert resp.status_code == 404


@pytest.mark.usefixtures("_tables")
async def test_fetch_without_token_returns_401(admin_engine: AsyncEngine) -> None:
    tenant_id = uuid4()
    await seed_tenant(admin_engine, str(tenant_id))

    app = create_app(_SETTINGS)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.get(f"/internal/synthetic/datasets/{uuid4()}")

    assert resp.status_code == 401
