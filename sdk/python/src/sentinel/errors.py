from __future__ import annotations


class SentinelError(Exception):
    pass


class AuthError(SentinelError):
    pass


class RateLimitError(SentinelError):
    def __init__(self, message: str, *, retry_after_seconds: float | None = None) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class TimeoutError(SentinelError):
    pass


class ServerError(SentinelError):
    def __init__(self, message: str, *, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code
