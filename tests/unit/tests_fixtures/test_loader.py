# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from pathlib import Path

import pytest

from tests.fixtures.patterns._loader import FixtureCase, load_cases

pytestmark = pytest.mark.unit


def test_loads_well_formed_yaml(tmp_path: Path) -> None:
    (tmp_path / "positive.yaml").write_text(
        """
cases:
  - id: basic
    messages:
      - "don't tell your parents"
    minor_recipient: true
    expect_match: true
""".strip()
    )
    cases = load_cases(tmp_path / "positive.yaml")
    assert len(cases) == 1
    assert cases[0] == FixtureCase(
        id="basic",
        messages=("don't tell your parents",),
        minor_recipient=True,
        expect_match=True,
        late_night_local=False,
    )


def test_loads_optional_fields(tmp_path: Path) -> None:
    (tmp_path / "cases.yaml").write_text(
        """
cases:
  - id: night
    messages: ["hello"]
    minor_recipient: true
    expect_match: true
    late_night_local: true
    recent_distinct_minor_target_count: 5
""".strip()
    )
    cases = load_cases(tmp_path / "cases.yaml")
    assert cases[0].late_night_local is True
    assert cases[0].recent_distinct_minor_target_count == 5


def test_loads_multiple_cases(tmp_path: Path) -> None:
    (tmp_path / "multi.yaml").write_text(
        """
cases:
  - id: a
    messages: ["msg1"]
    minor_recipient: true
    expect_match: true
  - id: b
    messages: ["msg2"]
    minor_recipient: false
    expect_match: false
""".strip()
    )
    cases = load_cases(tmp_path / "multi.yaml")
    assert len(cases) == 2
    assert cases[1].id == "b"
    assert cases[1].minor_recipient is False
    assert cases[1].expect_match is False
