# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from typing import Any

from shared.llm.fake import FakeProvider
from shared.synthetic.stages import STAGE_PROMPTS


def make_fake_provider() -> FakeProvider:
    responses: dict[str, dict[str, Any]] = {}
    for stage, prompt in STAGE_PROMPTS.items():
        responses[prompt] = {"text": f"safe reply for {stage.value}"}
    return FakeProvider(responses=responses)
