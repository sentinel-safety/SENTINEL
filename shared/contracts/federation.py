# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import datetime
from uuid import UUID

from shared.schemas.base import FrozenModel


class PublishRequest(FrozenModel):
    tenant_id: UUID
    actor_id: UUID
    signal_kinds: tuple[str, ...]
    flagged_at: datetime


class PublishResponse(FrozenModel):
    entry_id: str


class FeedSignalItem(FrozenModel):
    id: UUID
    publisher_tenant_id: UUID
    signal_kinds: tuple[str, ...]
    flagged_at: datetime


class FeedResponse(FrozenModel):
    signals: tuple[FeedSignalItem, ...]


class ReportFalseRequest(FrozenModel):
    signal_id: UUID
    reporter_tenant_id: UUID
    reason: str


class ReportFalseResponse(FrozenModel):
    status: str
