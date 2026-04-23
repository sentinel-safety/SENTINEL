# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

from services.synthetic_data.app.main import create_app
from shared.llm.fake import FakeProvider
from shared.synthetic.axes import GroomingStage
from shared.synthetic.stages import STAGE_PROMPTS
from tests.integration._phase7b_helpers import (
    fast_settings,
    make_access_token,
    seed_tenant,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

_AXES = {
    "demographics": [{"age_band": "14-15", "gender": "male", "regional_context": "UK"}],
    "platforms": ["dm"],
    "communication_styles": ["casual_typing"],
    "languages": ["en"],
}
_STAGE_MIX = {"weights": {stage.value: 1 for stage in GroomingStage}}

_SETTINGS = fast_settings()


def _fake_provider() -> FakeProvider:
    return FakeProvider(
        responses={
            prompt: {"text": f"safe reply for {stage.value}"}
            for stage, prompt in STAGE_PROMPTS.items()
        }
    )


def _researcher_headers(tenant_id: UUID) -> dict[str, str]:
    token = make_access_token(uuid4(), tenant_id, role="researcher")
    return {"Authorization": f"Bearer {token}"}


def _viewer_headers(tenant_id: UUID) -> dict[str, str]:
    token = make_access_token(uuid4(), tenant_id, role="viewer")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def _tables(clean_tables: None) -> None:
    pass


@pytest.mark.usefixtures("_tables")
async def test_generate_researcher_creates_run(admin_engine: AsyncEngine) -> None:
    tenant_id = uuid4()
    await seed_tenant(admin_engine, str(tenant_id))

    app = create_app(_SETTINGS)
    app.state.llm_provider = _fake_provider()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post(
            "/internal/synthetic/generate",
            json={"axes": _AXES, "stage_mix": _STAGE_MIX, "count": 3, "seed": 42},
            headers=_researcher_headers(tenant_id),
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "completed"
    assert body["count"] == 3
    assert UUID(body["run_id"])


@pytest.mark.usefixtures("_tables")
async def test_generate_viewer_gets_403(admin_engine: AsyncEngine) -> None:
    tenant_id = uuid4()
    await seed_tenant(admin_engine, str(tenant_id))

    app = create_app(_SETTINGS)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        resp = await client.post(
            "/internal/synthetic/generate",
            json={"axes": _AXES, "stage_mix": _STAGE_MIX, "count": 3, "seed": 42},
            headers=_viewer_headers(tenant_id),
        )

    assert resp.status_code == 403


@pytest.mark.usefixtures("_tables")
async def test_generate_then_fetch_dataset(admin_engine: AsyncEngine) -> None:
    tenant_id = uuid4()
    await seed_tenant(admin_engine, str(tenant_id))

    app = create_app(_SETTINGS)
    app.state.llm_provider = _fake_provider()
    headers = _researcher_headers(tenant_id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as client:
        gen_resp = await client.post(
            "/internal/synthetic/generate",
            json={"axes": _AXES, "stage_mix": _STAGE_MIX, "count": 4, "seed": 7},
            headers=headers,
        )
        assert gen_resp.status_code == 201
        run_id = gen_resp.json()["run_id"]

        fetch_resp = await client.get(
            f"/internal/synthetic/datasets/{run_id}",
            headers=headers,
        )

    assert fetch_resp.status_code == 200
    dataset = fetch_resp.json()
    assert len(dataset["conversations"]) == 4
    assert dataset["seed"] == 7
