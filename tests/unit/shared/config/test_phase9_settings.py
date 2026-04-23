# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.config.settings import Settings
from shared.schemas.enums import Jurisdiction

pytestmark = pytest.mark.unit


def test_honeypot_allowlist_default_empty() -> None:
    assert Settings().honeypot_jurisdiction_allowlist == ()


def test_honeypot_tier_threshold_default() -> None:
    assert Settings().honeypot_tier_threshold == 4


def test_honeypot_base_url_default() -> None:
    assert Settings().honeypot_base_url == "http://127.0.0.1:8010"


def test_honeypot_personas_dir_default() -> None:
    assert Settings().honeypot_personas_dir == "services/honeypot/personas"


def test_honeypot_allowlist_accepts_tuple() -> None:
    settings = Settings(honeypot_jurisdiction_allowlist=(Jurisdiction.US, Jurisdiction.UK))
    assert settings.honeypot_jurisdiction_allowlist == (Jurisdiction.US, Jurisdiction.UK)
