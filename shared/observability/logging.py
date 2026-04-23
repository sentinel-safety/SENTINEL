# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import logging
from typing import Any, cast

import orjson
import structlog
from opentelemetry import trace
from structlog.stdlib import BoundLogger
from structlog.types import EventDict, WrappedLogger

from shared.config import Settings

_configured: bool = False


def _serialize(obj: Any, default: Any = None) -> str:
    return orjson.dumps(obj, default=default, option=orjson.OPT_NON_STR_KEYS).decode()


def _inject_trace_context(_logger: WrappedLogger, _method: str, event_dict: EventDict) -> EventDict:
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx.is_valid:
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict


def configure_logging(settings: Settings) -> None:
    global _configured

    level = logging.getLevelNamesMapping()[settings.log_level]

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _inject_trace_context,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    renderer: Any = (
        structlog.dev.ConsoleRenderer(colors=False)
        if settings.env == "dev"
        else structlog.processors.JSONRenderer(serializer=_serialize)
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        root.addHandler(handler)

    _configured = True


def get_logger(name: str | None = None) -> BoundLogger:
    return cast(BoundLogger, structlog.get_logger(name))


def reset_logging() -> None:
    global _configured
    structlog.reset_defaults()
    _configured = False
