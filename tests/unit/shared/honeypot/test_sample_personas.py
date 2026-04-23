# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from pathlib import Path

import pytest

from shared.honeypot.personas import PersonaLoader

pytestmark = pytest.mark.unit

_DIR = Path("services/honeypot/personas")
_EXPECTED = (
    "emma-13-us-east",
    "liam-12-us-west",
    "sophia-14-us-south",
    "noah-13-uk",
    "ava-11-ca",
    "jackson-14-au",
)


def test_all_sample_personas_parse() -> None:
    loader = PersonaLoader(_DIR)
    for pid in _EXPECTED:
        p = loader.get(pid)
        assert p.consent_statement == "SYNTHETIC — not a real child"
        assert 9 <= p.age <= 17


def test_loader_lists_exactly_expected_ids() -> None:
    loader = PersonaLoader(_DIR)
    assert set(loader.list_ids()) == set(_EXPECTED)
