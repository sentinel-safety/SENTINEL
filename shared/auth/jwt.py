# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

import jwt

from shared.schemas.base import FrozenModel, UtcDatetime

TokenType = Literal["access", "refresh"]
Role = Literal["admin", "mod", "viewer", "auditor", "researcher"]
_ALGORITHM = "RS256"


class TokenError(Exception):
    pass


class TokenClaims(FrozenModel):
    user_id: UUID
    tenant_id: UUID
    role: Role
    token_type: TokenType
    issued_at: UtcDatetime
    expires_at: UtcDatetime


def issue_token(
    *,
    private_key_pem: str,
    user_id: UUID,
    tenant_id: UUID,
    role: Role,
    token_type: TokenType,
    issued_at: datetime,
    expires_at: datetime,
) -> str:
    payload = {
        "sub": str(user_id),
        "tid": str(tenant_id),
        "role": role,
        "typ": token_type,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, private_key_pem, algorithm=_ALGORITHM)


def decode_token(token: str, *, public_key_pem: str, expected_type: TokenType) -> TokenClaims:
    try:
        payload = jwt.decode(
            token,
            public_key_pem,
            algorithms=[_ALGORITHM],
            options={"require": ["sub", "tid", "role", "typ", "iat", "exp"]},
        )
    except jwt.PyJWTError as exc:
        raise TokenError(f"invalid token: {exc}") from exc
    if payload["typ"] != expected_type:
        raise TokenError(f"wrong token type: {payload['typ']} != {expected_type}")
    if payload["role"] not in ("admin", "mod", "viewer", "auditor", "researcher"):
        raise TokenError(f"unknown role: {payload['role']}")
    return TokenClaims(
        user_id=UUID(payload["sub"]),
        tenant_id=UUID(payload["tid"]),
        role=payload["role"],
        token_type=payload["typ"],
        issued_at=datetime.fromtimestamp(int(payload["iat"]), tz=UTC),
        expires_at=datetime.fromtimestamp(int(payload["exp"]), tz=UTC),
    )
