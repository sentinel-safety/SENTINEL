# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from shared.config.settings import Settings


def generate_keypair() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )
    return private_pem, public_pem


def load_keypair(settings: Settings) -> tuple[str, str]:
    priv = settings.dashboard_jwt_private_key_pem
    pub = settings.dashboard_jwt_public_key_pem
    if priv is None and pub is None:
        return generate_keypair()
    if priv is None or pub is None:
        raise ValueError(
            "dashboard_jwt_private_key_pem and dashboard_jwt_public_key_pem "
            "must both be set or both be unset"
        )
    return priv, pub
