# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, Request, status

from services.dashboard_bff.app.schemas import DashboardRole, SessionUser
from shared.auth.jwt import TokenError, decode_token
from shared.auth.keys import load_keypair

_BEARER_PREFIX = "Bearer "


async def get_current_user(
    request: Request,
    authorization: str = Header(default="", alias="Authorization"),
) -> SessionUser:
    if not authorization.startswith(_BEARER_PREFIX):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization[len(_BEARER_PREFIX) :]
    _, public_pem = load_keypair(request.app.state.settings)
    try:
        claims = decode_token(token, public_key_pem=public_pem, expected_type="access")
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return SessionUser(
        id=claims.user_id,
        tenant_id=claims.tenant_id,
        email="",
        role=DashboardRole(claims.role),
        display_name="",
    )


def require_roles(*allowed: DashboardRole) -> Callable[..., SessionUser]:
    allowed_set = frozenset(allowed)

    def _dep(current_user: SessionUser = Depends(get_current_user)) -> SessionUser:
        if current_user.role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"role {current_user.role.value} not permitted",
            )
        return current_user

    return _dep
