# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jsonschema import ValidationError, validate

from shared.llm.provider import LLMCallError, LLMValidationError


@dataclass
class FakeProvider:
    responses: dict[str, dict[str, Any]]

    async def complete(self, *, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        if prompt not in self.responses:
            raise LLMCallError(f"no fake response for prompt key {prompt!r}")
        payload = self.responses[prompt]
        try:
            validate(payload, schema)
        except ValidationError as exc:
            raise LLMValidationError(str(exc)) from exc
        return payload
