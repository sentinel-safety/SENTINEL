# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID, uuid5

import orjson
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from shared.federation.pepper import hash_actor, load_or_create_tenant_secret
from shared.federation.publisher_repository import get_publisher
from shared.federation.signals import FederationSignal, FederationSignalEnvelope
from shared.federation.signing import sign_signal
from shared.vector.qdrant_client import QdrantAdapter

_FP_NAMESPACE = UUID("1b3c3a3a-4d22-4b77-93a8-1d4e5f2c9e11")


def _point_id(tenant_id: UUID, actor_id: UUID) -> str:
    return str(uuid5(_FP_NAMESPACE, f"{tenant_id}:{actor_id}"))


async def _load_fingerprint(
    adapter: QdrantAdapter,
    *,
    tenant_id: UUID,
    actor_id: UUID,
) -> tuple[float, ...] | None:
    result = await adapter.client.retrieve(
        collection_name=adapter.collection_name,
        ids=[_point_id(tenant_id, actor_id)],
        with_vectors=True,
    )
    if not result:
        return None
    point = result[0]
    vec = point.vector
    if vec is None:
        return None
    return tuple(float(v) for v in vec)  # type: ignore[arg-type]


async def build_federation_signal(
    *,
    session: AsyncSession,
    tenant_id: UUID,
    actor_id: UUID,
    signal_kinds: tuple[str, ...],
    flagged_at: datetime,
    adapter: QdrantAdapter,
) -> FederationSignalEnvelope:
    tenant_secret = await load_or_create_tenant_secret(session, tenant_id=tenant_id)
    actor_hash = hash_actor(actor_id=actor_id, pepper=tenant_secret.actor_pepper)
    publisher = await get_publisher(session, tenant_id=tenant_id)
    if publisher is None:
        raise ValueError(f"no publisher record found for tenant {tenant_id}")
    fingerprint = await _load_fingerprint(adapter, tenant_id=tenant_id, actor_id=actor_id)
    if fingerprint is None:
        raise ValueError(f"no fingerprint found for actor {actor_id} in tenant {tenant_id}")
    signal = FederationSignal(
        publisher_tenant_id=tenant_id,
        actor_hash=actor_hash,
        fingerprint=fingerprint,
        signal_kinds=signal_kinds,
        flagged_at=flagged_at,
    )
    commit = sign_signal(secret=publisher.hmac_secret, signal=signal)
    return FederationSignalEnvelope(signal=signal, commit=commit)


def _envelope_to_dict(envelope: FederationSignalEnvelope) -> dict[str, Any]:
    sig = envelope.signal
    return {
        "signal": {
            "publisher_tenant_id": str(sig.publisher_tenant_id),
            "actor_hash": sig.actor_hash.hex(),
            "fingerprint": list(sig.fingerprint),
            "signal_kinds": list(sig.signal_kinds),
            "flagged_at": sig.flagged_at.isoformat(),
            "schema_version": sig.schema_version,
        },
        "commit": envelope.commit.hex(),
    }


async def publish_signal(
    *,
    redis: Redis[bytes],
    stream_name: str,
    envelope: FederationSignalEnvelope,
) -> str:
    payload = orjson.dumps(_envelope_to_dict(envelope))
    entry_id: str = await redis.xadd(stream_name, {"envelope": payload})
    return entry_id
