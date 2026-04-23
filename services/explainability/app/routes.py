# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header, HTTPException

from shared.db.session import tenant_session
from shared.explainability.reasoning_repository import (
    get_reasoning_for_event,
    list_reasoning_for_actor,
)
from shared.schemas.base import FrozenModel
from shared.schemas.reasoning import Reasoning

router = APIRouter(prefix="/internal", tags=["reasoning"])

_DEFAULT_LIMIT: int = 20


class ReasoningListResponse(FrozenModel):
    reasoning: tuple[Reasoning, ...]


@router.get("/reasoning/actor/{actor_id}", response_model=ReasoningListResponse)
async def reasoning_for_actor(
    actor_id: UUID,
    x_sentinel_tenant_id: UUID = Header(..., alias="x-sentinel-tenant-id"),
) -> ReasoningListResponse:
    async with tenant_session(x_sentinel_tenant_id) as session:
        rows = await list_reasoning_for_actor(
            session,
            tenant_id=x_sentinel_tenant_id,
            actor_id=actor_id,
            limit=_DEFAULT_LIMIT,
        )
    return ReasoningListResponse(reasoning=rows)


@router.get("/reasoning/event/{event_id}", response_model=Reasoning)
async def reasoning_for_event(
    event_id: UUID,
    x_sentinel_tenant_id: UUID = Header(..., alias="x-sentinel-tenant-id"),
) -> Reasoning:
    async with tenant_session(x_sentinel_tenant_id) as session:
        found = await get_reasoning_for_event(
            session,
            tenant_id=x_sentinel_tenant_id,
            event_id=event_id,
        )
    if found is None:
        raise HTTPException(status_code=404, detail="reasoning not found")
    return found
