# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models import Event as EventRow
from shared.db.models import PatternMatch as PatternMatchRow
from shared.schemas.base import FrozenModel, UtcDatetime
from shared.scoring.signals import SignalKind

_PATTERN_NAME_TO_SIGNAL: dict[str, SignalKind] = {
    "secrecy_request": SignalKind.SECRECY_REQUEST,
    "platform_migration": SignalKind.PLATFORM_MIGRATION_REQUEST,
    "personal_info_probe": SignalKind.PERSONAL_INFO_PROBE,
    "gift_offering": SignalKind.GIFT_OFFERING,
    "exclusivity": SignalKind.EXCLUSIVITY,
    "exclusivity_llm": SignalKind.EXCLUSIVITY,
    "late_night": SignalKind.LATE_NIGHT_MINOR_CONTACT,
    "multi_minor_contact": SignalKind.MULTI_MINOR_CONTACT_WINDOW,
    "friendship_forming": SignalKind.FRIENDSHIP_FORMING,
    "risk_assessment": SignalKind.RISK_ASSESSMENT,
    "isolation": SignalKind.ISOLATION,
    "desensitization": SignalKind.DESENSITIZATION,
    "sexual_escalation": SignalKind.SEXUAL_ESCALATION,
    "cross_session_escalation": SignalKind.CROSS_SESSION_ESCALATION,
    "behavioral_fingerprint_match": SignalKind.BEHAVIORAL_FINGERPRINT_MATCH,
    "suspicious_cluster_membership": SignalKind.SUSPICIOUS_CLUSTER_MEMBERSHIP,
}


class ActorMemoryView(FrozenModel):
    distinct_conversations_last_window: int
    distinct_minor_targets_last_window: int
    pattern_counts_by_kind: dict[SignalKind, int]
    stages_observed: tuple[str, ...]
    first_contact_at: UtcDatetime | None
    most_recent_contact_at: UtcDatetime | None
    total_events_last_window: int


async def get_actor_memory(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    actor_id: UUID,
    now: datetime,
    lookback: timedelta,
) -> ActorMemoryView:
    since = now - lookback
    event_stmt = select(
        EventRow.conversation_id,
        EventRow.target_actor_ids,
        EventRow.content_features,
        EventRow.timestamp,
    ).where(
        EventRow.tenant_id == tenant_id,
        EventRow.actor_id == actor_id,
        EventRow.timestamp >= since,
    )
    distinct_conversations: set[str] = set()
    distinct_minor_targets: set[str] = set()
    total_events = 0
    first_ts: datetime | None = None
    last_ts: datetime | None = None
    for row in (await session.execute(event_stmt)).all():
        total_events += 1
        distinct_conversations.add(str(row.conversation_id))
        is_minor = bool((row.content_features or {}).get("minor_recipient"))
        if is_minor:
            for target in row.target_actor_ids or ():
                distinct_minor_targets.add(str(target))
        ts = row.timestamp
        if first_ts is None or ts < first_ts:
            first_ts = ts
        if last_ts is None or ts > last_ts:
            last_ts = ts

    pm_stmt = (
        select(
            PatternMatchRow.pattern_id,
            PatternMatchRow.stage,
            func.count().label("n"),
        )
        .where(
            PatternMatchRow.tenant_id == tenant_id,
            PatternMatchRow.actor_id == actor_id,
            PatternMatchRow.matched_at >= since,
        )
        .group_by(PatternMatchRow.pattern_id, PatternMatchRow.stage)
    )
    counts: dict[SignalKind, int] = {}
    stages: set[str] = set()
    for row in (await session.execute(pm_stmt)).all():
        kind = _PATTERN_NAME_TO_SIGNAL.get(row.pattern_id)
        if kind is not None:
            counts[kind] = counts.get(kind, 0) + int(row.n)
        if row.stage is not None:
            stages.add(row.stage)

    return ActorMemoryView(
        distinct_conversations_last_window=len(distinct_conversations),
        distinct_minor_targets_last_window=len(distinct_minor_targets),
        pattern_counts_by_kind=counts,
        stages_observed=tuple(sorted(stages)),
        first_contact_at=first_ts,
        most_recent_contact_at=last_ts,
        total_events_last_window=total_events,
    )
