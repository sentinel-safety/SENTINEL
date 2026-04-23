# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends, HTTPException, status

_ALLOWED_ROLES: frozenset[str] = frozenset({"researcher", "admin"})


def authorized_researcher_check(role: str) -> bool:
    return role in _ALLOWED_ROLES


def require_researcher(
    role_dep: Callable[..., Coroutine[Any, Any, str]],
) -> Callable[..., Coroutine[Any, Any, str]]:
    async def _dep(role: str = Depends(role_dep)) -> str:
        if not authorized_researcher_check(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"role '{role}' is not permitted for synthetic data access",
            )
        return role

    return _dep
