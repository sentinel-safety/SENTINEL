# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.auth.keys import generate_keypair, load_keypair
from shared.config.settings import Settings

pytestmark = pytest.mark.unit


def test_generates_ephemeral_keypair_when_unset() -> None:
    settings = Settings(env="dev")
    priv, pub = load_keypair(settings)
    assert "PRIVATE" in priv.upper()
    assert "BEGIN" in priv
    assert "PUBLIC" in pub.upper()
    assert "BEGIN" in pub


def test_uses_provided_keypair_when_set() -> None:
    priv, pub = generate_keypair()
    settings = Settings(
        dashboard_jwt_private_key_pem=priv,
        dashboard_jwt_public_key_pem=pub,
    )
    got_priv, got_pub = load_keypair(settings)
    assert got_priv == priv
    assert got_pub == pub


def test_mismatched_partial_config_raises() -> None:
    priv, _ = generate_keypair()
    settings = Settings(dashboard_jwt_private_key_pem=priv)
    with pytest.raises(ValueError):
        load_keypair(settings)
