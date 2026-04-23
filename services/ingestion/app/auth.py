# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import os
from uuid import UUID

from fastapi import Header, HTTPException, status

from shared.auth.api_key import ResolvedApiKey, resolve_api_key


def _test_bypass_enabled() -> bool:
    return os.environ.get("SENTINEL_INGESTION_AUTH_TEST_BYPASS") == "1"


async def require_api_key(
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> ResolvedApiKey:
    if _test_bypass_enabled():
        return ResolvedApiKey(
            id=UUID(int=0),
            tenant_id=UUID(int=0),
            scope="write",
            prefix="sk_test",
        )
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing Authorization bearer token",
            headers={"WWW-Authenticate": 'Bearer realm="sentinel"'},
        )
    token = authorization.split(" ", 1)[1].strip()
    resolved = await resolve_api_key(token)
    if resolved is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid api key",
            headers={"WWW-Authenticate": 'Bearer realm="sentinel"'},
        )
    if resolved.scope == "read":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="api key lacks write scope",
        )
    return resolved
