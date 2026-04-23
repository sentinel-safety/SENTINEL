# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.llm.fake import FakeProvider
from shared.llm.provider import LLMValidationError

pytestmark = [pytest.mark.unit, pytest.mark.asyncio]


async def test_returns_registered_response() -> None:
    provider = FakeProvider(
        responses={"grooming:friendship": {"confidence": 0.8, "evidence": ["x"]}}
    )
    schema = {
        "type": "object",
        "required": ["confidence", "evidence"],
        "properties": {
            "confidence": {"type": "number"},
            "evidence": {"type": "array", "items": {"type": "string"}},
        },
    }
    result = await provider.complete(prompt="grooming:friendship", schema=schema)
    assert result["confidence"] == 0.8


async def test_validates_against_schema() -> None:
    provider = FakeProvider(responses={"bad": {"confidence": "not-a-number"}})
    schema = {
        "type": "object",
        "required": ["confidence"],
        "properties": {"confidence": {"type": "number"}},
    }
    with pytest.raises(LLMValidationError):
        await provider.complete(prompt="bad", schema=schema)
