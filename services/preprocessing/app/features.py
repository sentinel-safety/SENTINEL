# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from shared.contracts.preprocess import ExtractedFeatures
from shared.schemas.enums import AgeBand
from shared.schemas.event import Event

_WHITESPACE_RE = re.compile(r"\s+")
_URL_RE = re.compile(r"https?://|www\.|\b\S+\.(?:com|net|gg|io|me|tk|xyz|link)\b", re.IGNORECASE)
_CONTACT_RE = re.compile(
    r"\b(?:phone|number|address|snap|discord|whatsapp|signal|telegram|instagram|"
    r"insta|ig|tiktok|what's your|whats your|where do you live|what school)\b",
    re.IGNORECASE,
)
_MINOR_BANDS: frozenset[AgeBand] = frozenset(
    {AgeBand.UNDER_13, AgeBand.BAND_13_15, AgeBand.BAND_16_17}
)
_LATE_NIGHT_START: int = 22
_LATE_NIGHT_END: int = 6


def normalize(content: str) -> str:
    return _WHITESPACE_RE.sub(" ", content.strip()).lower()


def _detect_language(content: str) -> str:
    try:
        import langdetect  # type: ignore[import-not-found]
    except ImportError:
        return "unknown"
    try:
        return str(langdetect.detect(content)) if content.strip() else "unknown"
    except Exception:
        return "unknown"


def _is_minor_recipient(age_bands: tuple[AgeBand, ...]) -> bool:
    return any(band in _MINOR_BANDS for band in age_bands)


def _is_late_night(timestamp: datetime, timezone_name: str) -> bool:
    local = timestamp.astimezone(ZoneInfo(timezone_name))
    hour = local.hour
    return hour >= _LATE_NIGHT_START or hour < _LATE_NIGHT_END


def extract_features(
    *,
    event: Event,
    content: str,
    recipient_age_bands: tuple[AgeBand, ...],
    recipient_timezone: str,
) -> ExtractedFeatures:
    normalized = normalize(content)
    tokens = [token for token in normalized.split(" ") if token]
    return ExtractedFeatures(
        normalized_content=normalized,
        language=_detect_language(content),
        token_count=len(tokens),
        contains_url=bool(_URL_RE.search(content)),
        contains_contact_request=bool(_CONTACT_RE.search(content)),
        minor_recipient=_is_minor_recipient(recipient_age_bands),
        late_night_local=_is_late_night(event.timestamp, recipient_timezone),
    )
