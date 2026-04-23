# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

from shared.contracts.preprocess import ExtractedFeatures
from shared.patterns.matches import PatternMatch
from shared.schemas.base import FrozenModel
from shared.schemas.event import Event


class DetectRequest(FrozenModel):
    event: Event
    features: ExtractedFeatures


class DetectResponse(FrozenModel):
    matches: tuple[PatternMatch, ...] = ()
    matched_ids: tuple[UUID, ...] = ()
