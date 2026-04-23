# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from services.ingestion.app.auth import require_api_key
from services.ingestion.app.clients import DownstreamClients
from services.ingestion.app.service import IngestionService
from shared.auth.api_key import ResolvedApiKey
from shared.contracts.ingest import ActorStateResponse, IngestEventRequest, IngestEventResponse
from shared.db.models import SuspicionProfile as SuspicionProfileRow
from shared.db.session import tenant_session
from shared.schemas.enums import ResponseTier

router = APIRouter(prefix="/v1", tags=["ingest"])


def _clients_dependency(request: Request) -> DownstreamClients:
    clients: DownstreamClients = request.app.state.downstream_clients
    return clients


@router.post("/events", response_model=IngestEventResponse)
async def ingest_event(
    payload: IngestEventRequest,
    api_key: ResolvedApiKey = Depends(require_api_key),
    clients: DownstreamClients = Depends(_clients_dependency),
) -> IngestEventResponse:
    from uuid import UUID as _UUID

    if api_key.tenant_id != _UUID(int=0) and payload.tenant_id != api_key.tenant_id:
        raise HTTPException(
            status_code=403,
            detail="api key does not match tenant in payload",
        )
    service = IngestionService(clients=clients)
    try:
        return await service.handle(payload)
    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail="invalid tenant or actor reference") from exc


@router.get("/actors/{actor_id}", response_model=ActorStateResponse)
async def get_actor(
    actor_id: UUID,
    x_tenant_id: UUID = Header(alias="x-tenant-id"),
) -> ActorStateResponse:
    async with tenant_session(x_tenant_id) as session:
        result = await session.execute(
            select(SuspicionProfileRow).where(
                SuspicionProfileRow.tenant_id == x_tenant_id,
                SuspicionProfileRow.actor_id == actor_id,
            )
        )
        row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="actor not found")
    return ActorStateResponse(
        actor_id=row.actor_id,
        tenant_id=row.tenant_id,
        current_score=row.current_score,
        tier=ResponseTier(row.tier),
        last_updated=row.last_updated,
    )
