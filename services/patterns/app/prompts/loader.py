# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from pathlib import Path

_DEFAULT_PROMPTS_ROOT = Path(__file__).parents[2] / "prompts"


class PromptNotFoundError(FileNotFoundError):
    pass


def load_prompt(
    name: str,
    version: str,
    *,
    prompts_root: Path = _DEFAULT_PROMPTS_ROOT,
) -> str:
    path = prompts_root / name / f"{version}.md"
    if not path.exists():
        raise PromptNotFoundError(f"{name}/{version}.md not found at {path}")
    return path.read_text()
