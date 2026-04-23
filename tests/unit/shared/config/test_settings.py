# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from pathlib import Path

import pytest

from shared.config.settings import Settings

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[4]
ENV_EXAMPLE = REPO_ROOT / ".env.example"


def test_defaults_point_at_local_stack() -> None:
    s = Settings()
    assert "asyncpg" in s.postgres_dsn
    assert "psycopg" in s.postgres_sync_dsn
    assert s.redis_dsn.startswith("redis://")
    assert s.env == "dev"
    assert s.log_level == "INFO"


def test_env_overrides_pick_up(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SENTINEL_ENV", "prod")
    monkeypatch.setenv("SENTINEL_LOG_LEVEL", "WARNING")
    monkeypatch.setenv("SENTINEL_DB_POOL_SIZE", "42")
    s = Settings()
    assert s.env == "prod"
    assert s.log_level == "WARNING"
    assert s.db_pool_size == 42


def test_rejects_wrong_scheme() -> None:
    with pytest.raises(ValueError):
        Settings(postgres_dsn="mysql://x:y@z/db")


def test_get_settings_is_cached() -> None:
    from shared.config import get_settings

    assert get_settings() is get_settings()


def test_env_example_documents_every_setting() -> None:
    body = ENV_EXAMPLE.read_text(encoding="utf-8")
    for field_name in Settings.model_fields:
        token = f"SENTINEL_{field_name.upper()}"
        assert token in body, f"{token} missing from .env.example"
