# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest
from jinja2 import UndefinedError

from shared.explainability.evidence_templates import render_evidence

pytestmark = pytest.mark.unit


def test_missing_variable_raises() -> None:
    with pytest.raises(UndefinedError):
        render_evidence(pattern_name="platform_migration", variables={})


def test_unknown_pattern_raises_key_error() -> None:
    with pytest.raises(KeyError):
        render_evidence(pattern_name="does_not_exist", variables={})
