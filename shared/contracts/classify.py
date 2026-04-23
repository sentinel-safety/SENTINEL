# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from shared.contracts.preprocess import ExtractedFeatures
from shared.schemas.base import FrozenModel
from shared.schemas.event import Event
from shared.scoring.signals import ScoreSignal


class ClassifyRequest(FrozenModel):
    event: Event
    features: ExtractedFeatures


class ClassifyResponse(FrozenModel):
    signals: tuple[ScoreSignal, ...] = ()
