# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import hmac
from hashlib import sha256

from shared.federation.signals import FederationSignal, canonical_bytes


def sign_signal(*, secret: bytes, signal: FederationSignal) -> bytes:
    return hmac.new(secret, canonical_bytes(signal), sha256).digest()


def verify_signal(*, secret: bytes, signal: FederationSignal, commit: bytes) -> bool:
    expected = sign_signal(secret=secret, signal=signal)
    return hmac.compare_digest(expected, commit)
