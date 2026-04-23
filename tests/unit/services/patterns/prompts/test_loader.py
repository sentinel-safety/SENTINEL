# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from pathlib import Path

import pytest

from services.patterns.app.prompts.loader import PromptNotFoundError, load_prompt

pytestmark = pytest.mark.unit


def test_loads_existing_prompt(tmp_path: Path) -> None:
    prompts_root = tmp_path / "prompts"
    prompt_file = prompts_root / "test_pattern" / "v1.md"
    prompt_file.parent.mkdir(parents=True)
    prompt_file.write_text("You are a detector.\n")
    result = load_prompt("test_pattern", "v1", prompts_root=prompts_root)
    assert result == "You are a detector.\n"


def test_raises_on_missing_version(tmp_path: Path) -> None:
    prompts_root = tmp_path / "prompts"
    prompts_root.mkdir()
    with pytest.raises(PromptNotFoundError, match="v99"):
        load_prompt("test_pattern", "v99", prompts_root=prompts_root)


def test_raises_on_missing_pattern(tmp_path: Path) -> None:
    prompts_root = tmp_path / "prompts"
    prompts_root.mkdir()
    with pytest.raises(PromptNotFoundError, match="unknown_pattern"):
        load_prompt("unknown_pattern", "v1", prompts_root=prompts_root)


def test_default_prompts_root_resolves() -> None:
    text = load_prompt("friendship_forming", "v1")
    assert len(text) > 0
    assert "friendship" in text.lower() or "trust" in text.lower() or "rapport" in text.lower()
