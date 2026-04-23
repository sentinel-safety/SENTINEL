# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class FixtureCase:
    id: str
    messages: tuple[str, ...]
    minor_recipient: bool
    expect_match: bool
    late_night_local: bool = False
    recent_distinct_minor_target_count: int = 0


def load_recorded_responses(path: Path) -> dict[str, dict[str, dict[str, object]]]:
    raw = yaml.safe_load(path.read_text())
    return {pattern: dict(cases) for pattern, cases in raw.items()}


def load_cases(path: Path) -> tuple[FixtureCase, ...]:
    raw = yaml.safe_load(path.read_text())
    return tuple(
        FixtureCase(
            id=c["id"],
            messages=tuple(c["messages"]),
            minor_recipient=bool(c["minor_recipient"]),
            expect_match=bool(c["expect_match"]),
            late_night_local=bool(c.get("late_night_local", False)),
            recent_distinct_minor_target_count=int(c.get("recent_distinct_minor_target_count", 0)),
        )
        for c in raw["cases"]
    )
