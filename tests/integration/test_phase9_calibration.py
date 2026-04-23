# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import subprocess
import sys

import pytest

pytestmark = [pytest.mark.integration]


def test_phase9_measure_script_reports_no_false_positives() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/phase9_measure.py", "--sample-size", "50"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "FP=0" in result.stdout
    assert "TP_rate>=0.90" in result.stdout
