# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import json
import subprocess

import pytest

pytestmark = pytest.mark.integration


def test_checkpoint_thresholds() -> None:
    out = subprocess.check_output(["uv", "run", "python", "scripts/phase2_measure.py"])
    reports = json.loads(out)
    for r in reports:
        assert r["fp"] < 0.05, f"{r['slug']} FP={r['fp']}"
        assert r["tp"] > 0.70, f"{r['slug']} TP={r['tp']}"
        assert r["adversarial_fn"] < 0.40, f"{r['slug']} FN={r['adversarial_fn']}"
