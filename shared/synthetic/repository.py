# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models import SyntheticConversation, SyntheticRun
from shared.synthetic.axes import DiversityAxes, StageMix
from shared.synthetic.dataset import SyntheticConversation as SyntheticConversationSchema
from shared.synthetic.dataset import SyntheticDataset, SyntheticTurn


async def create_run(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    requested_by_user_id: UUID | None,
    seed: int,
    count: int,
    axes: DiversityAxes,
    stage_mix: StageMix,
) -> UUID:
    run_id = uuid4()
    run = SyntheticRun(
        id=run_id,
        tenant_id=tenant_id,
        requested_by_user_id=requested_by_user_id,
        seed=seed,
        count=count,
        axes=axes.model_dump(),
        stage_mix=stage_mix.model_dump(),
        status="pending",
    )
    session.add(run)
    await session.flush()
    return run_id


async def update_run_status(
    session: AsyncSession,
    run_id: UUID,
    *,
    status: str,
    error: str | None = None,
) -> None:
    now = datetime.now(UTC)
    values: dict[str, object] = {"status": status}
    if status == "running":
        values["started_at"] = now
    elif status in ("completed", "failed"):
        values["completed_at"] = now
    if error is not None:
        values["error"] = error
    await session.execute(update(SyntheticRun).where(SyntheticRun.id == run_id).values(**values))


async def insert_conversations(
    session: AsyncSession,
    run_id: UUID,
    tenant_id: UUID,
    conversations: tuple[SyntheticConversationSchema, ...],
) -> None:
    for conv in conversations:
        row = SyntheticConversation(
            id=conv.id,
            run_id=run_id,
            tenant_id=tenant_id,
            stage=conv.stage.value,
            demographics=conv.demographics.model_dump(),
            platform=conv.platform.value,
            communication_style=conv.communication_style.value,
            turns=[t.model_dump() for t in conv.turns],
        )
        session.add(row)
    await session.flush()


async def get_run(session: AsyncSession, run_id: UUID) -> SyntheticRun | None:
    result = await session.execute(select(SyntheticRun).where(SyntheticRun.id == run_id))
    return result.scalar_one_or_none()


async def list_conversations_for_run(
    session: AsyncSession, run_id: UUID
) -> list[SyntheticConversation]:
    result = await session.execute(
        select(SyntheticConversation).where(SyntheticConversation.run_id == run_id)
    )
    return list(result.scalars().all())


async def list_runs_for_tenant(session: AsyncSession, tenant_id: UUID) -> list[SyntheticRun]:
    result = await session.execute(select(SyntheticRun).where(SyntheticRun.tenant_id == tenant_id))
    return list(result.scalars().all())


def reconstruct_dataset(run: SyntheticRun, rows: list[SyntheticConversation]) -> SyntheticDataset:
    axes = DiversityAxes.model_validate(run.axes)
    stage_mix = StageMix.model_validate(run.stage_mix)
    conversations = tuple(
        SyntheticConversationSchema.model_validate(
            {
                "id": row.id,
                "stage": row.stage,
                "demographics": row.demographics,
                "platform": row.platform,
                "communication_style": row.communication_style,
                "language": (row.demographics or {}).get("regional_context", "en"),
                "turns": [SyntheticTurn.model_validate(t) for t in (row.turns or [])],
            }
        )
        for row in rows
    )
    return SyntheticDataset(
        run_id=run.id,
        seed=run.seed,
        axes=axes,
        stage_mix=stage_mix,
        conversations=conversations,
        generated_at=run.created_at,
        schema_version=1,
    )
