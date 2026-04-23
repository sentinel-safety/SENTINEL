# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from shared.config import Settings
from shared.observability.context import (
    bind_actor_id,
    bind_request_id,
    bind_tenant_id,
    clear_context,
    current_context,
    log_context,
)
from shared.observability.logging import (
    configure_logging,
    get_logger,
    reset_logging,
)
from shared.observability.tracing import (
    configure_tracing,
    get_tracer,
    instrument_fastapi,
    instrument_httpx_client,
    reset_tracing,
)


def configure_observability(settings: Settings) -> None:
    configure_logging(settings)
    configure_tracing(settings)


def reset_observability() -> None:
    reset_logging()
    reset_tracing()


__all__ = [
    "bind_actor_id",
    "bind_request_id",
    "bind_tenant_id",
    "clear_context",
    "configure_logging",
    "configure_observability",
    "configure_tracing",
    "current_context",
    "get_logger",
    "get_tracer",
    "instrument_fastapi",
    "instrument_httpx_client",
    "log_context",
    "reset_logging",
    "reset_observability",
    "reset_tracing",
]
