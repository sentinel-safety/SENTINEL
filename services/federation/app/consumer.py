# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import asyncio
import struct
from datetime import datetime
from uuid import UUID

import orjson
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from services.federation.app.qdrant_federated import FederatedQdrantAdapter
from shared.audit.events import record_federation_received
from shared.db.models import FederationPublisher
from shared.federation.publisher_repository import get_publisher, update_reputation
from shared.federation.reputation import ReputationDelta, adjust_reputation
from shared.federation.reputation_repository import insert_reputation_event
from shared.federation.signal_repository import insert_signal
from shared.federation.signals import FederationSignal, FederationSignalEnvelope
from shared.federation.signing import verify_signal

_GROUP = "federation-workers"
_CONSUMER = "consumer-1"


def _parse_envelope(raw: bytes) -> FederationSignalEnvelope | None:
    try:
        data = orjson.loads(raw)
        sig_data = data["signal"]
        signal = FederationSignal(
            publisher_tenant_id=UUID(sig_data["publisher_tenant_id"]),
            actor_hash=bytes.fromhex(sig_data["actor_hash"]),
            fingerprint=tuple(sig_data["fingerprint"]),
            signal_kinds=tuple(sig_data["signal_kinds"]),
            flagged_at=datetime.fromisoformat(sig_data["flagged_at"]),
            schema_version=sig_data.get("schema_version", 1),
        )
        commit = bytes.fromhex(data["commit"])
        return FederationSignalEnvelope(signal=signal, commit=commit)
    except Exception:
        return None


async def _ensure_group(redis: Redis[bytes], stream_name: str) -> None:
    try:
        await redis.xgroup_create(stream_name, _GROUP, id="0", mkstream=True)
    except Exception as exc:
        if "BUSYGROUP" not in str(exc):
            raise


async def _handle_invalid_signature(
    session: AsyncSession,
    *,
    publisher: FederationPublisher,
    redis: Redis[bytes],
    stream_name: str,
    entry_id: bytes,
) -> None:
    new_rep = adjust_reputation(publisher.reputation, ReputationDelta.SIGNATURE_INVALID.name)
    await update_reputation(session, tenant_id=publisher.tenant_id, reputation=new_rep)
    await insert_reputation_event(
        session,
        publisher_tenant_id=publisher.tenant_id,
        reporter_tenant_id=publisher.tenant_id,
        delta=ReputationDelta.SIGNATURE_INVALID,
        reason="SIGNATURE_INVALID",
    )
    await redis.xack(stream_name, _GROUP, entry_id)  # type: ignore[no-untyped-call]


async def _handle_valid_signal(
    session: AsyncSession,
    *,
    envelope: FederationSignalEnvelope,
    publisher: FederationPublisher,
    qdrant_adapter: FederatedQdrantAdapter,
    redis: Redis[bytes],
    stream_name: str,
    entry_id: bytes,
    receiver_tenant_id: UUID,
) -> None:
    sig = envelope.signal
    fp_bytes = struct.pack(f"{len(sig.fingerprint)}f", *sig.fingerprint)
    signal_id = await insert_signal(
        session,
        publisher_tenant_id=sig.publisher_tenant_id,
        fingerprint_bytes=fp_bytes,
        signal_kinds=sig.signal_kinds,
        flagged_at=sig.flagged_at,
        commit=envelope.commit,
    )
    await qdrant_adapter.upsert_signal(
        signal_id=signal_id,
        fingerprint=sig.fingerprint,
        publisher_tenant_id=sig.publisher_tenant_id,
        actor_hash=sig.actor_hash.hex(),
        flagged_at=sig.flagged_at,
        reputation=publisher.reputation,
    )
    await record_federation_received(
        session,
        receiver_tenant_id=receiver_tenant_id,
        publisher_tenant_id=sig.publisher_tenant_id,
        signal_id=signal_id,
        actor_hash=sig.actor_hash.hex(),
    )
    await redis.xack(stream_name, _GROUP, entry_id)  # type: ignore[no-untyped-call]


async def run_federation_consumer(
    redis: Redis[bytes],
    *,
    stream_name: str,
    qdrant_adapter: FederatedQdrantAdapter,
    session: AsyncSession,
    receiver_tenant_id: UUID,
    stop_event: asyncio.Event,
    iteration_limit: int | None = None,
) -> None:
    await _ensure_group(redis, stream_name)
    iterations = 0
    while not stop_event.is_set():
        if iteration_limit is not None and iterations >= iteration_limit:
            break
        entries = await redis.xreadgroup(_GROUP, _CONSUMER, {stream_name: ">"}, count=10, block=0)
        if not entries:
            iterations += 1
            continue
        for _stream, messages in entries:
            for entry_id, fields in messages:
                raw = fields.get(b"envelope")
                if raw is None:
                    await redis.xack(stream_name, _GROUP, entry_id)  # type: ignore[no-untyped-call]
                    continue
                envelope = _parse_envelope(raw)
                if envelope is None:
                    await redis.xack(stream_name, _GROUP, entry_id)  # type: ignore[no-untyped-call]
                    continue
                publisher = await get_publisher(
                    session, tenant_id=envelope.signal.publisher_tenant_id
                )
                if publisher is None or publisher.revoked_at is not None:
                    await redis.xack(stream_name, _GROUP, entry_id)  # type: ignore[no-untyped-call]
                    continue
                valid = verify_signal(
                    secret=publisher.hmac_secret,
                    signal=envelope.signal,
                    commit=envelope.commit,
                )
                if not valid:
                    await _handle_invalid_signature(
                        session,
                        publisher=publisher,
                        redis=redis,
                        stream_name=stream_name,
                        entry_id=entry_id,
                    )
                    continue
                await _handle_valid_signal(
                    session,
                    envelope=envelope,
                    publisher=publisher,
                    qdrant_adapter=qdrant_adapter,
                    redis=redis,
                    stream_name=stream_name,
                    entry_id=entry_id,
                    receiver_tenant_id=receiver_tenant_id,
                )
        iterations += 1
