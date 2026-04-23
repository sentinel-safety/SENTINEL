# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.llm.provider import LLMCallError, LLMProvider, LLMValidationError

pytestmark = pytest.mark.unit


def test_errors_are_distinct() -> None:
    assert issubclass(LLMValidationError, LLMCallError)


def test_provider_is_protocol() -> None:
    assert hasattr(LLMProvider, "complete")
