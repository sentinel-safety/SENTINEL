# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import csv
import io
import zipfile
from collections.abc import Mapping, Sequence
from typing import Any

import orjson


def _csv_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    if not rows:
        return b""
    buf = io.StringIO()
    fieldnames = list(rows[0].keys())
    writer = csv.DictWriter(buf, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in fieldnames})
    return buf.getvalue().encode("utf-8")


def _jsonl_bytes(rows: Sequence[Mapping[str, Any]]) -> bytes:
    if not rows:
        return b""
    return b"\n".join(orjson.dumps(row) for row in rows) + b"\n"


def build_export_zip(
    categories: Mapping[str, Sequence[Mapping[str, Any]]],
) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, rows in sorted(categories.items()):
            zf.writestr(f"{name}.csv", _csv_bytes(rows))
            zf.writestr(f"{name}.jsonl", _jsonl_bytes(rows))
    return buf.getvalue()
