# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.explainability.evidence_templates import render_evidence

pytestmark = pytest.mark.unit


def test_render_platform_migration() -> None:
    out = render_evidence(
        pattern_name="platform_migration",
        variables={"matched_phrase": "let's move to Telegram"},
    )
    assert "Telegram" in out
    assert "let's move to Telegram" in out


def test_render_personal_info_probe() -> None:
    out = render_evidence(
        pattern_name="personal_info_probe",
        variables={"matched_phrase": "what school"},
    )
    assert "what school" in out
