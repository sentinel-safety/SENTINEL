# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.config.settings import Settings
from shared.llm.anthropic_provider import AnthropicProvider
from shared.llm.factory import MissingAPIKeyError, build_llm_provider
from shared.llm.fake import FakeProvider
from shared.llm.openai_provider import OpenAIProvider
from shared.llm.provider import LLMProvider

pytestmark = pytest.mark.unit


def _settings(monkeypatch: pytest.MonkeyPatch, **overrides: str | None) -> Settings:
    env_map = {
        "llm_default_provider": "SENTINEL_LLM_DEFAULT_PROVIDER",
        "anthropic_api_key": "SENTINEL_ANTHROPIC_API_KEY",  # pragma: allowlist secret
        "openai_api_key": "SENTINEL_OPENAI_API_KEY",  # pragma: allowlist secret
        "llm_timeout_seconds": "SENTINEL_LLM_TIMEOUT_SECONDS",
    }
    for key, value in overrides.items():
        env_var = env_map[key]
        if value is None:
            monkeypatch.delenv(env_var, raising=False)
        else:
            monkeypatch.setenv(env_var, value)
    return Settings()


def test_fake_provider_is_default(monkeypatch: pytest.MonkeyPatch) -> None:
    s = _settings(monkeypatch, llm_default_provider="fake")
    provider = build_llm_provider(s)
    assert isinstance(provider, FakeProvider)


def test_anthropic_provider_built_with_key(monkeypatch: pytest.MonkeyPatch) -> None:
    s = _settings(
        monkeypatch,
        llm_default_provider="anthropic",
        anthropic_api_key="sk-ant-key",  # pragma: allowlist secret
        llm_timeout_seconds="10.0",
    )
    provider = build_llm_provider(s)
    assert isinstance(provider, AnthropicProvider)


def test_anthropic_raises_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    s = _settings(monkeypatch, llm_default_provider="anthropic", anthropic_api_key=None)
    with pytest.raises(MissingAPIKeyError):
        build_llm_provider(s)


def test_openai_provider_built_with_key(monkeypatch: pytest.MonkeyPatch) -> None:
    s = _settings(
        monkeypatch,
        llm_default_provider="openai",
        openai_api_key="sk-openai-key",  # pragma: allowlist secret
        llm_timeout_seconds="15.0",
    )
    provider = build_llm_provider(s)
    assert isinstance(provider, OpenAIProvider)


def test_openai_raises_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    s = _settings(monkeypatch, llm_default_provider="openai", openai_api_key=None)
    with pytest.raises(MissingAPIKeyError):
        build_llm_provider(s)


def test_timeout_is_passed_to_anthropic(monkeypatch: pytest.MonkeyPatch) -> None:
    s = _settings(
        monkeypatch,
        llm_default_provider="anthropic",
        anthropic_api_key="sk-ant-key",  # pragma: allowlist secret
        llm_timeout_seconds="42.0",
    )
    provider = build_llm_provider(s)
    assert isinstance(provider, AnthropicProvider)
    assert provider._timeout == 42.0


def test_timeout_is_passed_to_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    s = _settings(
        monkeypatch,
        llm_default_provider="openai",
        openai_api_key="sk-openai-key",  # pragma: allowlist secret
        llm_timeout_seconds="7.5",
    )
    provider = build_llm_provider(s)
    assert isinstance(provider, OpenAIProvider)
    assert provider._timeout == 7.5


def test_all_providers_satisfy_protocol(monkeypatch: pytest.MonkeyPatch) -> None:
    providers = [
        build_llm_provider(_settings(monkeypatch, llm_default_provider="fake")),
        build_llm_provider(
            _settings(
                monkeypatch,
                llm_default_provider="anthropic",
                anthropic_api_key="sk-ant-key",  # pragma: allowlist secret
            )
        ),
        build_llm_provider(
            _settings(
                monkeypatch,
                llm_default_provider="openai",
                openai_api_key="sk-openai-key",  # pragma: allowlist secret
            )
        ),
    ]
    for provider in providers:
        assert isinstance(provider, LLMProvider)
