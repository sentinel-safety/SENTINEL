# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


class LLMCallError(Exception):
    pass


class LLMValidationError(LLMCallError):
    pass


@runtime_checkable
class LLMProvider(Protocol):
    async def complete(self, *, prompt: str, schema: dict[str, Any]) -> dict[str, Any]: ...
