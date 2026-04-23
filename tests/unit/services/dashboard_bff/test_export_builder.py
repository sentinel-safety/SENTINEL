# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import io
import zipfile

import pytest

from services.dashboard_bff.app.export_builder import build_export_zip

pytestmark = pytest.mark.unit


def test_zip_contains_one_csv_and_one_jsonl_per_category() -> None:
    buf = build_export_zip(
        {
            "audit_log": [{"id": "1", "event_type": "x"}],
            "suspicion_profiles": [{"actor_id": "a", "tier": 2}],
        }
    )
    with zipfile.ZipFile(io.BytesIO(buf)) as z:
        names = sorted(z.namelist())
    assert names == [
        "audit_log.csv",
        "audit_log.jsonl",
        "suspicion_profiles.csv",
        "suspicion_profiles.jsonl",
    ]


def test_empty_category_produces_empty_files() -> None:
    buf = build_export_zip({"audit_log": []})
    with zipfile.ZipFile(io.BytesIO(buf)) as z:
        assert z.read("audit_log.csv") == b""
        assert z.read("audit_log.jsonl") == b""


def test_csv_rows_written_in_order() -> None:
    rows = [{"a": "1", "b": "2"}, {"a": "3", "b": "4"}]
    buf = build_export_zip({"events": rows})
    with zipfile.ZipFile(io.BytesIO(buf)) as z:
        csv_txt = z.read("events.csv").decode("utf-8").splitlines()
    assert csv_txt[0] == "a,b"
    assert csv_txt[1] == "1,2"
    assert csv_txt[2] == "3,4"
