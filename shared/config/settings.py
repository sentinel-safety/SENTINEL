# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.schemas.enums import Jurisdiction


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="SENTINEL_",
        extra="ignore",
        case_sensitive=False,
    )

    env: Literal["dev", "test", "staging", "prod"] = "dev"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    service_name: str = "sentinel"

    postgres_dsn: str = Field(
        default="postgresql+asyncpg://sentinel_app:sentinel_app_dev@127.0.0.1:5432/sentinel",  # pragma: allowlist secret
        pattern=r"^postgresql\+(asyncpg|psycopg)://",
    )
    postgres_sync_dsn: str = Field(
        default="postgresql+psycopg://sentinel:sentinel_dev@127.0.0.1:5432/sentinel",  # pragma: allowlist secret
        pattern=r"^postgresql\+psycopg://",
    )
    redis_dsn: str = Field(default="redis://127.0.0.1:6379/0", pattern=r"^redis://")
    qdrant_url: str = "http://127.0.0.1:6333"
    otlp_endpoint: str = "http://127.0.0.1:4317"

    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_statement_timeout_ms: int = 5000

    preprocess_base_url: str = "http://127.0.0.1:8002"
    classifier_first_pass_base_url: str = "http://127.0.0.1:8003"  # noqa: S105
    scoring_base_url: str = "http://127.0.0.1:8004"
    patterns_base_url: str = "http://127.0.0.1:8005"
    memory_base_url: str = "http://127.0.0.1:8001"
    memory_lookback_days: int = Field(default=21, ge=1, le=365)

    graph_base_url: str = "http://127.0.0.1:8006"
    graph_lookback_days: int = Field(default=7, ge=1, le=90)
    qdrant_fingerprint_collection: str = "actor_fingerprints"
    fingerprint_vector_dim: int = Field(default=16, ge=4, le=256)
    fingerprint_similarity_threshold: float = Field(default=0.85, gt=0.0, le=1.0)
    cluster_min_flagged_neighbors: int = Field(default=2, ge=1, le=50)
    fingerprint_search_top_k: int = Field(default=10, ge=1, le=100)

    patterns_llm_queue_name: str = "patterns:llm-queue"

    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    llm_default_provider: Literal["anthropic", "openai", "fake"] = "fake"
    llm_timeout_seconds: float = 5.0

    response_base_url: str = "http://127.0.0.1:8007"
    response_tier_change_stream: str = "response:tier_changes"
    response_retry_stream: str = "response:retry_queue"
    response_dead_letter_stream: str = "response:dead_letter"
    response_retry_max_attempts: int = Field(default=5, ge=1, le=20)
    response_retry_base_delay_seconds: float = Field(default=2.0, gt=0.0, le=60.0)
    response_retry_max_delay_seconds: float = Field(default=60.0, gt=0.0, le=600.0)
    response_hmac_timestamp_skew_seconds: int = Field(default=300, ge=30, le=3600)
    response_worker_block_ms: int = Field(default=2000, ge=100, le=30000)

    reasoning_retention_days: int = Field(default=90, ge=1, le=3650)

    dashboard_bff_base_url: str = "http://127.0.0.1:8009"
    dashboard_jwt_private_key_pem: str | None = None
    dashboard_jwt_public_key_pem: str | None = None
    dashboard_access_token_ttl_minutes: int = Field(default=30, ge=1, le=720)
    dashboard_refresh_token_ttl_days: int = Field(default=14, ge=1, le=90)
    dashboard_argon2_time_cost: int = Field(default=3, ge=1, le=10)
    dashboard_argon2_memory_cost: int = Field(default=65536, ge=8, le=1048576)
    dashboard_argon2_parallelism: int = Field(default=1, ge=1, le=16)

    honeypot_base_url: str = "http://127.0.0.1:8010"
    honeypot_personas_dir: str = "services/honeypot/personas"
    honeypot_tier_threshold: int = Field(default=4, ge=0, le=5)
    honeypot_jurisdiction_allowlist: tuple[Jurisdiction, ...] = Field(default=())

    federation_enabled_globally: bool = False
    federation_signals_stream: str = "federation:signals"
    federation_qdrant_collection: str = "federated_fingerprints"
    federation_publish_tier_threshold: str = "restrict"
    federation_advisory_delta: int = 10
    federation_low_reputation_delta: int = 3
    federation_low_reputation_threshold: int = 30
    federation_base_url: str = "http://127.0.0.1:8011"
    federation_consumer_block_ms: int = 2000

    synthetic_base_url: str = "http://127.0.0.1:8012"
    synthetic_researcher_token_ttl_minutes: int = 60
    synthetic_default_seed: int = 424242


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
