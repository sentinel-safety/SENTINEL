# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from shared.synthetic.axes import (
    CommunicationStyle,
    Demographics,
    DiversityAxes,
    GroomingStage,
    Platform,
    StageMix,
)
from shared.synthetic.dataset import SyntheticConversation, SyntheticTurn
from shared.synthetic.repository import (
    create_run,
    get_run,
    insert_conversations,
    list_conversations_for_run,
    list_runs_for_tenant,
    update_run_status,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


async def _seed_tenant(engine: AsyncEngine, tenant_id: UUID) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO tenant (id, name, tier, compliance_jurisdictions, "
                "data_retention_days, feature_flags) "
                "VALUES (:t, 'repo-test', 'free', '{}', 30, '{}'::jsonb) "
                "ON CONFLICT DO NOTHING"
            ),
            {"t": str(tenant_id)},
        )


async def _tenant_session(app_engine: AsyncEngine, tenant_id: UUID) -> AsyncSession:
    factory = async_sessionmaker(bind=app_engine, expire_on_commit=False, autoflush=False)
    s = factory()
    await s.begin()
    await s.execute(text("SELECT set_config('app.tenant_id', :tid, true)"), {"tid": str(tenant_id)})
    return s


@pytest.fixture
def _tables(clean_tables: None) -> None:
    pass


def _axes() -> DiversityAxes:
    return DiversityAxes(
        demographics=(Demographics(age_band="14-15", gender="male", regional_context="UK"),),
        platforms=(Platform.DM,),
        communication_styles=(CommunicationStyle.CASUAL_TYPING,),
        languages=("en",),
    )


def _mix() -> StageMix:
    return StageMix(weights=dict.fromkeys(GroomingStage, 1))


def _make_conversations(count: int) -> tuple[SyntheticConversation, ...]:
    stages = list(GroomingStage)
    return tuple(
        SyntheticConversation(
            id=uuid4(),
            stage=stages[i % len(stages)],
            demographics=Demographics(age_band="14-15", gender="male", regional_context="UK"),
            platform=Platform.DM,
            communication_style=CommunicationStyle.CASUAL_TYPING,
            language="en",
            turns=(
                SyntheticTurn(role="actor", text="hello there", timestamp_offset_seconds=0),
                SyntheticTurn(role="target", text="hi", timestamp_offset_seconds=10),
            ),
        )
        for i in range(count)
    )


@pytest.mark.usefixtures("_tables")
async def test_create_run_and_fetch(admin_engine: AsyncEngine, app_engine: AsyncEngine) -> None:
    tenant_id = uuid4()
    await _seed_tenant(admin_engine, tenant_id)
    session = await _tenant_session(app_engine, tenant_id)
    async with session:
        run_id = await create_run(
            session,
            tenant_id=tenant_id,
            requested_by_user_id=None,
            seed=42,
            count=10,
            axes=_axes(),
            stage_mix=_mix(),
        )
        run = await get_run(session, run_id)
        assert run is not None
        assert run.tenant_id == tenant_id
        assert run.seed == 42
        assert run.count == 10
        assert run.status == "pending"


@pytest.mark.usefixtures("_tables")
async def test_update_run_status(admin_engine: AsyncEngine, app_engine: AsyncEngine) -> None:
    tenant_id = uuid4()
    await _seed_tenant(admin_engine, tenant_id)
    session = await _tenant_session(app_engine, tenant_id)
    async with session:
        run_id = await create_run(
            session,
            tenant_id=tenant_id,
            requested_by_user_id=None,
            seed=1,
            count=5,
            axes=_axes(),
            stage_mix=_mix(),
        )
        await update_run_status(session, run_id, status="running")
        run = await get_run(session, run_id)
        assert run is not None
        assert run.status == "running"
        assert run.started_at is not None

        await update_run_status(session, run_id, status="completed")
        run = await get_run(session, run_id)
        assert run is not None
        assert run.status == "completed"
        assert run.completed_at is not None


@pytest.mark.usefixtures("_tables")
async def test_insert_and_list_conversations(
    admin_engine: AsyncEngine, app_engine: AsyncEngine
) -> None:
    tenant_id = uuid4()
    await _seed_tenant(admin_engine, tenant_id)
    session = await _tenant_session(app_engine, tenant_id)
    async with session:
        run_id = await create_run(
            session,
            tenant_id=tenant_id,
            requested_by_user_id=None,
            seed=99,
            count=10,
            axes=_axes(),
            stage_mix=_mix(),
        )
        convs = _make_conversations(10)
        await insert_conversations(session, run_id, tenant_id, convs)
        rows = await list_conversations_for_run(session, run_id)
        assert len(rows) == 10
        assert all(r.run_id == run_id for r in rows)
        assert all(r.tenant_id == tenant_id for r in rows)


@pytest.mark.usefixtures("_tables")
async def test_list_runs_for_tenant(admin_engine: AsyncEngine, app_engine: AsyncEngine) -> None:
    tenant_id = uuid4()
    await _seed_tenant(admin_engine, tenant_id)
    session = await _tenant_session(app_engine, tenant_id)
    async with session:
        for i in range(3):
            await create_run(
                session,
                tenant_id=tenant_id,
                requested_by_user_id=None,
                seed=i,
                count=5,
                axes=_axes(),
                stage_mix=_mix(),
            )
        runs = await list_runs_for_tenant(session, tenant_id)
        assert len(runs) == 3


@pytest.mark.usefixtures("_tables")
async def test_roundtrip_conversations_match(
    admin_engine: AsyncEngine, app_engine: AsyncEngine
) -> None:
    tenant_id = uuid4()
    await _seed_tenant(admin_engine, tenant_id)
    session = await _tenant_session(app_engine, tenant_id)
    async with session:
        run_id = await create_run(
            session,
            tenant_id=tenant_id,
            requested_by_user_id=None,
            seed=7,
            count=10,
            axes=_axes(),
            stage_mix=_mix(),
        )
        convs = _make_conversations(10)
        await insert_conversations(session, run_id, tenant_id, convs)
        rows = await list_conversations_for_run(session, run_id)
        returned_ids = {r.id for r in rows}
        original_ids = {c.id for c in convs}
        assert returned_ids == original_ids
