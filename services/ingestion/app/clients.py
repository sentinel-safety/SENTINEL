# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from dataclasses import dataclass

import httpx

from shared.config import Settings
from shared.contracts.patterns import DetectRequest, DetectResponse
from shared.contracts.preprocess import ExtractedFeatures, PreprocessRequest, PreprocessResponse
from shared.contracts.score import ScoreRequest, ScoreResponse
from shared.schemas.enums import AgeBand
from shared.schemas.event import Event
from shared.scoring.signals import ScoreSignal


@dataclass
class DownstreamClients:
    settings: Settings
    http: httpx.AsyncClient
    preprocess_url: str
    patterns_url: str
    score_url: str

    @classmethod
    def from_settings(cls, settings: Settings, http: httpx.AsyncClient) -> DownstreamClients:
        return cls(
            settings=settings,
            http=http,
            preprocess_url=settings.preprocess_base_url,
            patterns_url=settings.patterns_base_url,
            score_url=settings.scoring_base_url,
        )

    async def preprocess(
        self,
        *,
        event: Event,
        content: str,
        recipient_age_bands: tuple[AgeBand, ...],
        recipient_timezone: str,
    ) -> PreprocessResponse:
        body = PreprocessRequest(
            event=event,
            content=content,
            recipient_age_bands=recipient_age_bands,
            recipient_timezone=recipient_timezone,
        ).model_dump(mode="json")
        response = await self.http.post(f"{self.preprocess_url}/internal/preprocess", json=body)
        response.raise_for_status()
        return PreprocessResponse.model_validate(response.json())

    async def detect(self, *, event: Event, features: ExtractedFeatures) -> DetectResponse:
        body = DetectRequest(event=event, features=features).model_dump(mode="json")
        response = await self.http.post(f"{self.patterns_url}/internal/detect", json=body)
        response.raise_for_status()
        return DetectResponse.model_validate(response.json())

    async def score(self, *, event: Event, signals: tuple[ScoreSignal, ...]) -> ScoreResponse:
        body = ScoreRequest(event=event, signals=signals).model_dump(mode="json")
        response = await self.http.post(f"{self.score_url}/internal/score", json=body)
        response.raise_for_status()
        return ScoreResponse.model_validate(response.json())
