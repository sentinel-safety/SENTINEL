# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from shared.auth.jwt import TokenClaims, TokenError, decode_token, issue_token
from shared.auth.keys import generate_keypair

pytestmark = pytest.mark.unit


def _keys() -> tuple[str, str]:
    return generate_keypair()


def test_issue_and_decode_round_trip() -> None:
    priv, pub = _keys()
    uid = uuid.uuid4()
    tid = uuid.uuid4()
    now = datetime.now(UTC)
    token = issue_token(
        private_key_pem=priv,
        user_id=uid,
        tenant_id=tid,
        role="admin",
        token_type="access",
        issued_at=now,
        expires_at=now + timedelta(minutes=30),
    )
    claims = decode_token(token, public_key_pem=pub, expected_type="access")
    assert claims.user_id == uid
    assert claims.tenant_id == tid
    assert claims.role == "admin"
    assert claims.token_type == "access"


def test_decode_rejects_expired_token() -> None:
    priv, pub = _keys()
    past = datetime.now(UTC) - timedelta(hours=2)
    token = issue_token(
        private_key_pem=priv,
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        role="mod",
        token_type="access",
        issued_at=past - timedelta(minutes=30),
        expires_at=past,
    )
    with pytest.raises(TokenError):
        decode_token(token, public_key_pem=pub, expected_type="access")


def test_decode_rejects_tampered_signature() -> None:
    priv, pub = _keys()
    now = datetime.now(UTC)
    token = issue_token(
        private_key_pem=priv,
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        role="viewer",
        token_type="access",
        issued_at=now,
        expires_at=now + timedelta(minutes=30),
    )
    head, payload, sig = token.split(".")
    bad = f"{head}.{payload}.{'A' * len(sig)}"
    with pytest.raises(TokenError):
        decode_token(bad, public_key_pem=pub, expected_type="access")


def test_decode_rejects_wrong_token_type() -> None:
    priv, pub = _keys()
    now = datetime.now(UTC)
    token = issue_token(
        private_key_pem=priv,
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        role="admin",
        token_type="refresh",
        issued_at=now,
        expires_at=now + timedelta(days=14),
    )
    with pytest.raises(TokenError):
        decode_token(token, public_key_pem=pub, expected_type="access")


def test_claims_model_is_frozen() -> None:
    claims = TokenClaims(
        user_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        role="admin",
        token_type="access",
        issued_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(minutes=1),
    )
    with pytest.raises((TypeError, ValueError)):
        claims.role = "mod"  # type: ignore[misc]
