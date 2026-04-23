# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from pydantic import Field

from shared.schemas.base import FrozenModel
from shared.schemas.enums import AgeBand
from shared.schemas.event import Event


class ExtractedFeatures(FrozenModel):
    normalized_content: str = Field(max_length=10_000)
    language: str = Field(min_length=2, max_length=10)
    token_count: int = Field(ge=0)
    contains_url: bool
    contains_contact_request: bool
    minor_recipient: bool
    late_night_local: bool


class PreprocessRequest(FrozenModel):
    event: Event
    content: str = Field(max_length=20_000)
    recipient_age_bands: tuple[AgeBand, ...] = ()
    recipient_timezone: str = Field(default="UTC", max_length=64)


class PreprocessResponse(FrozenModel):
    features: ExtractedFeatures
