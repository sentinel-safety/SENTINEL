# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter

from shared.contracts.memory import MemoryLookupRequest, MemoryLookupResponse
from shared.db.session import tenant_session
from shared.memory import get_actor_memory

router = APIRouter(prefix="/internal", tags=["memory"])


@router.post("/actor-memory", response_model=MemoryLookupResponse)
async def actor_memory(payload: MemoryLookupRequest) -> MemoryLookupResponse:
    now = datetime.now(UTC)
    async with tenant_session(payload.tenant_id) as session:
        view = await get_actor_memory(
            session,
            tenant_id=payload.tenant_id,
            actor_id=payload.actor_id,
            now=now,
            lookback=timedelta(days=payload.lookback_days),
        )
    return MemoryLookupResponse(view=view)
