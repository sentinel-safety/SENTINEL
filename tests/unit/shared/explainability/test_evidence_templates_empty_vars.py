# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.explainability.evidence_templates import render_evidence

pytestmark = pytest.mark.unit


def test_late_night_template_renders_without_vars() -> None:
    out = render_evidence(pattern_name="late_night", variables={})
    assert "late" in out.lower()
