# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from typing import Any
from uuid import UUID


class SentinelError(Exception):
    """Base class for every domain error raised inside sentinel services."""

    http_status: int = 500
    code: str = "sentinel.internal_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict[str, Any] = details or {}

    def to_payload(self) -> dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": self.details}


class ValidationError(SentinelError):
    http_status = 400
    code = "sentinel.validation_error"


class AuthError(SentinelError):
    http_status = 401
    code = "sentinel.auth_error"


class InvalidApiKeyError(AuthError):
    code = "sentinel.auth.invalid_api_key"


class InsufficientScopeError(AuthError):
    http_status = 403
    code = "sentinel.auth.insufficient_scope"


class TenantError(SentinelError):
    http_status = 404
    code = "sentinel.tenant_error"


class TenantNotFoundError(TenantError):
    code = "sentinel.tenant.not_found"

    def __init__(self, tenant_id: UUID) -> None:
        super().__init__(f"tenant {tenant_id} not found", details={"tenant_id": str(tenant_id)})


class TenantQuotaExceededError(TenantError):
    http_status = 429
    code = "sentinel.tenant.quota_exceeded"


class ActorError(SentinelError):
    http_status = 404
    code = "sentinel.actor_error"


class ActorNotFoundError(ActorError):
    code = "sentinel.actor.not_found"

    def __init__(self, actor_id: UUID, tenant_id: UUID) -> None:
        super().__init__(
            f"actor {actor_id} not found for tenant {tenant_id}",
            details={"actor_id": str(actor_id), "tenant_id": str(tenant_id)},
        )


class EventError(SentinelError):
    http_status = 400
    code = "sentinel.event_error"


class DuplicateEventError(EventError):
    http_status = 409
    code = "sentinel.event.duplicate"


class InvalidEventError(EventError):
    code = "sentinel.event.invalid"


class PatternError(SentinelError):
    code = "sentinel.pattern_error"


class PatternNotFoundError(PatternError):
    http_status = 404
    code = "sentinel.pattern.not_found"


class PatternExecutionError(PatternError):
    code = "sentinel.pattern.execution_error"


class ScoringError(SentinelError):
    code = "sentinel.scoring_error"


class ScoreOutOfRangeError(ScoringError):
    code = "sentinel.scoring.out_of_range"


class DecayError(ScoringError):
    code = "sentinel.scoring.decay_error"


class LlmError(SentinelError):
    http_status = 502
    code = "sentinel.llm_error"


class LlmTimeoutError(LlmError):
    http_status = 504
    code = "sentinel.llm.timeout"


class LlmRateLimitedError(LlmError):
    http_status = 429
    code = "sentinel.llm.rate_limited"


class LlmUnavailableError(LlmError):
    http_status = 503
    code = "sentinel.llm.unavailable"


class AuditError(SentinelError):
    code = "sentinel.audit_error"


class AuditChainBrokenError(AuditError):
    code = "sentinel.audit.chain_broken"


class AuditTamperedError(AuditError):
    code = "sentinel.audit.tampered"


class RateLimitedError(SentinelError):
    http_status = 429
    code = "sentinel.rate_limited"


class ServiceDegradedError(SentinelError):
    http_status = 503
    code = "sentinel.service.degraded"
