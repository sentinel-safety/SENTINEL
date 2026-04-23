from __future__ import annotations

from sentinel._version import __version__
from sentinel.client import SentinelClient
from sentinel.errors import (
    AuthError,
    RateLimitError,
    SentinelError,
    ServerError,
    TimeoutError,
)
from sentinel.events import EventsAPI
from sentinel.models import (
    ActionKind,
    EventType,
    PrimaryDriver,
    Reasoning,
    RecommendedAction,
    ResponseTier,
    ScoreResult,
)
from sentinel.webhooks import WebhookSignatureError, verify_webhook_signature

__all__ = [
    "ActionKind",
    "AuthError",
    "EventType",
    "EventsAPI",
    "PrimaryDriver",
    "RateLimitError",
    "Reasoning",
    "RecommendedAction",
    "ResponseTier",
    "ScoreResult",
    "SentinelClient",
    "SentinelError",
    "ServerError",
    "TimeoutError",
    "WebhookSignatureError",
    "__version__",
    "verify_webhook_signature",
]
