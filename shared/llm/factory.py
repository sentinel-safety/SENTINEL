# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from shared.config.settings import Settings
from shared.llm.anthropic_provider import AnthropicProvider
from shared.llm.fake import FakeProvider
from shared.llm.openai_provider import OpenAIProvider
from shared.llm.provider import LLMProvider


class MissingAPIKeyError(Exception):
    pass


def build_llm_provider(settings: Settings) -> LLMProvider:
    name = settings.llm_default_provider
    timeout = settings.llm_timeout_seconds

    if name == "anthropic":
        if not settings.anthropic_api_key:
            raise MissingAPIKeyError(
                "SENTINEL_ANTHROPIC_API_KEY is required for anthropic provider"
            )
        return AnthropicProvider(settings.anthropic_api_key, timeout_seconds=timeout)

    if name == "openai":
        if not settings.openai_api_key:
            raise MissingAPIKeyError("SENTINEL_OPENAI_API_KEY is required for openai provider")
        return OpenAIProvider(settings.openai_api_key, timeout_seconds=timeout)

    return FakeProvider(responses={})
