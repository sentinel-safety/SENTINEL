# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from services.dashboard_bff.app.schemas import SessionUser
from services.synthetic_data.app.dependencies import require_researcher_or_admin
from shared.config import get_settings
from shared.contracts.synthetic import GenerateRequest, GenerateResponse
from shared.db.session import tenant_session
from shared.llm.factory import build_llm_provider
from shared.llm.provider import LLMProvider
from shared.synthetic.axes import DiversityAxes, StageMix
from shared.synthetic.dataset import SyntheticDataset
from shared.synthetic.pipeline import generate_dataset
from shared.synthetic.repository import (
    create_run,
    get_run,
    insert_conversations,
    list_conversations_for_run,
    reconstruct_dataset,
    update_run_status,
)

router = APIRouter(prefix="/internal/synthetic", tags=["synthetic"])

_require_auth = require_researcher_or_admin()


def _get_llm_provider(request: Request) -> LLMProvider:
    override: LLMProvider | None = getattr(request.app.state, "llm_provider", None)
    if override is not None:
        return override
    return build_llm_provider(get_settings())


@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_201_CREATED)
async def generate(
    payload: GenerateRequest,
    request: Request,
    current_user: SessionUser = Depends(_require_auth),
) -> GenerateResponse:
    axes = DiversityAxes.model_validate(payload.axes)
    stage_mix = StageMix.model_validate(payload.stage_mix)

    async with tenant_session(current_user.tenant_id) as session:
        run_id = await create_run(
            session,
            tenant_id=current_user.tenant_id,
            requested_by_user_id=None,
            seed=payload.seed,
            count=payload.count,
            axes=axes,
            stage_mix=stage_mix,
        )
        await update_run_status(session, run_id, status="running")

    provider = _get_llm_provider(request)
    try:
        dataset = await generate_dataset(
            axes=axes,
            stage_mix=stage_mix,
            count=payload.count,
            seed=payload.seed,
            provider=provider,
            run_id=run_id,
        )
    except Exception as exc:
        async with tenant_session(current_user.tenant_id) as session:
            await update_run_status(session, run_id, status="failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="generation failed",
        ) from exc

    async with tenant_session(current_user.tenant_id) as session:
        await insert_conversations(session, run_id, current_user.tenant_id, dataset.conversations)
        await update_run_status(session, run_id, status="completed")

    return GenerateResponse(run_id=run_id, status="completed", count=len(dataset.conversations))


@router.get("/datasets/{run_id}", response_model=SyntheticDataset)
async def fetch_dataset(
    run_id: UUID,
    current_user: SessionUser = Depends(_require_auth),
) -> SyntheticDataset:
    async with tenant_session(current_user.tenant_id) as session:
        run = await get_run(session, run_id)
        if run is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
        rows = await list_conversations_for_run(session, run_id)

    return reconstruct_dataset(run, rows)
