# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.models import Event as EventRow
from shared.fingerprint.features import ActorFeatureWindow

_SECRECY_TOKENS = ("dont tell", "don't tell", "our secret", "keep it between us")
_PLATFORM_TOKENS = ("telegram", "signal", "snapchat", "whatsapp", "switch to", "move to")
_IMAGE_TOKENS = ("send a pic", "send me a photo", "send me a pic")
_VIDEO_TOKENS = ("send me a video", "webcam")
_COMPLIMENT_TOKENS = ("pretty", "beautiful", "gorgeous", "so mature", "so smart")
_GIFT_TOKENS = ("v-bucks", "gift card", "robux", "steam code")
_QUESTION_TOKEN = "?"  # noqa: S105


@dataclass
class WindowRow:
    timestamp: datetime
    target_actor_ids: list[str]
    conversation_id: UUID
    content_features: dict[str, Any]


async def fetch_window_rows(
    session: AsyncSession, *, tenant_id: UUID, actor_id: UUID, since: datetime
) -> list[WindowRow]:
    stmt = select(
        EventRow.timestamp,
        EventRow.target_actor_ids,
        EventRow.conversation_id,
        EventRow.content_features,
    ).where(
        EventRow.tenant_id == tenant_id,
        EventRow.actor_id == actor_id,
        EventRow.timestamp >= since,
    )
    rows = (await session.execute(stmt)).all()
    return [
        WindowRow(
            timestamp=r.timestamp,
            target_actor_ids=list(r.target_actor_ids or []),
            conversation_id=r.conversation_id,
            content_features=dict(r.content_features or {}),
        )
        for r in rows
    ]


def aggregate_window_from_rows(
    rows: Iterable[WindowRow], *, actor_id: UUID, now: datetime
) -> ActorFeatureWindow:
    total = 0
    compliments = 0
    questions = 0
    personal_info = 0
    late_night = 0
    minors = 0
    platform = 0
    secrecy = 0
    gifts = 0
    images = 0
    videos = 0
    urls = 0
    contacts = 0
    chars = 0
    distinct_conv: set[str] = set()
    distinct_targets: set[str] = set()

    for row in rows:
        total += 1
        distinct_conv.add(str(row.conversation_id))
        feats = row.content_features
        content = str(feats.get("normalized_content", ""))
        lower = content.lower()
        chars += len(content)
        if feats.get("minor_recipient"):
            minors += 1
            for t in row.target_actor_ids:
                distinct_targets.add(t)
        if feats.get("late_night_local"):
            late_night += 1
        if feats.get("contains_url"):
            urls += 1
        if feats.get("contains_contact_request"):
            contacts += 1
        if _QUESTION_TOKEN in content:
            questions += 1
        if any(token in lower for token in _COMPLIMENT_TOKENS):
            compliments += 1
        if any(token in lower for token in _SECRECY_TOKENS):
            secrecy += 1
        if any(token in lower for token in _PLATFORM_TOKENS):
            platform += 1
        if any(token in lower for token in _IMAGE_TOKENS):
            images += 1
        if any(token in lower for token in _VIDEO_TOKENS):
            videos += 1
        if any(token in lower for token in _GIFT_TOKENS):
            gifts += 1
        if "where do you live" in lower or "what school" in lower or "whats your" in lower:
            personal_info += 1

    return ActorFeatureWindow(
        total_messages=float(total),
        compliment_count=float(compliments),
        question_count=float(questions),
        personal_info_requests=float(personal_info),
        late_night_count=float(late_night),
        minor_recipient_count=float(minors),
        platform_migration_mentions=float(platform),
        secrecy_mentions=float(secrecy),
        distinct_minor_targets=float(len(distinct_targets)),
        total_chars=float(chars),
        distinct_conversations=float(len(distinct_conv)),
        url_mentions=float(urls),
        gift_mentions=float(gifts),
        image_requests=float(images),
        video_requests=float(videos),
        contact_requests=float(contacts),
    )
