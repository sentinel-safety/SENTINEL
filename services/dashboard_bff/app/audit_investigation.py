# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from shared.audit.chain import append_entry
from shared.db.models import AuditLogEntry
from shared.schemas.audit_log import AuditEventType


async def record_investigation_access(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    role: str,
    conversation_id: UUID,
    reason: str,
) -> AuditLogEntry:
    return await append_entry(
        session,
        tenant_id=tenant_id,
        event_type=AuditEventType.INVESTIGATION_CONTENT_ACCESS.value,
        timestamp=datetime.now(UTC),
        details={
            "user_id": str(user_id),
            "role": role,
            "conversation_id": str(conversation_id),
            "reason": reason,
            "break_glass": True,
        },
    )
