from __future__ import annotations

import pytest

MOCK_BASE_URL = "https://api.sentinel.test"
MOCK_API_KEY = "sk_test_123"  # pragma: allowlist secret


@pytest.fixture
def base_url() -> str:
    return MOCK_BASE_URL


@pytest.fixture
def api_key() -> str:
    return MOCK_API_KEY
