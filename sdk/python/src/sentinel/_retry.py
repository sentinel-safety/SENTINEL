from __future__ import annotations

from datetime import datetime
from email.utils import parsedate_to_datetime


def compute_backoff(*, attempt: int, base: float, cap: float) -> float:
    if attempt < 1:
        raise ValueError("attempt must be >= 1")
    return float(min(cap, base * (2 ** (attempt - 1))))


def parse_retry_after(value: str | None, *, now: datetime) -> float | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        seconds = float(value)
    except ValueError:
        seconds = None
    if seconds is not None:
        return max(0.0, seconds)
    try:
        target = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if target is None:
        return None
    delta = (target - now).total_seconds()
    return max(0.0, delta)
