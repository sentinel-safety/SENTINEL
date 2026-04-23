# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from uuid import UUID

from structlog.contextvars import (
    bind_contextvars,
    clear_contextvars,
    get_contextvars,
    reset_contextvars,
)


def bind_tenant_id(tenant_id: UUID) -> None:
    bind_contextvars(tenant_id=str(tenant_id))


def bind_request_id(request_id: str) -> None:
    bind_contextvars(request_id=request_id)


def bind_actor_id(actor_id: UUID) -> None:
    bind_contextvars(actor_id=str(actor_id))


def current_context() -> dict[str, Any]:
    return dict(get_contextvars())


def clear_context() -> None:
    clear_contextvars()


@contextmanager
def log_context(**bindings: Any) -> Iterator[None]:
    tokens = bind_contextvars(**bindings)
    try:
        yield
    finally:
        reset_contextvars(**tokens)
