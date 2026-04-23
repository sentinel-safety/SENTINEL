# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from dataclasses import dataclass

from services.ingestion.app.clients import DownstreamClients
from services.ingestion.app.intake import intake_event
from shared.contracts.ingest import IngestEventRequest, IngestEventResponse
from shared.db.session import tenant_session
from shared.patterns.matches import PatternMatch
from shared.schemas.enums import AgeBand
from shared.scoring.signals import ScoreSignal


def _to_signals(matches: tuple[PatternMatch, ...]) -> tuple[ScoreSignal, ...]:
    return tuple(
        ScoreSignal(
            kind=m.signal_kind,
            confidence=m.confidence,
            evidence=" | ".join(m.evidence_excerpts)[:500],
        )
        for m in matches
    )


@dataclass
class IngestionService:
    clients: DownstreamClients

    async def handle(self, payload: IngestEventRequest) -> IngestEventResponse:
        async with tenant_session(payload.tenant_id) as session:
            intake = await intake_event(session, payload)
        event = intake.event

        recipient_bands = tuple(
            AgeBand(b)
            for b in payload.metadata.get("recipient_age_bands", [])
            if b in AgeBand.__members__.values()
        )
        recipient_tz = str(payload.metadata.get("recipient_timezone", "UTC"))

        preprocess_resp = await self.clients.preprocess(
            event=event,
            content=payload.content,
            recipient_age_bands=recipient_bands,
            recipient_timezone=recipient_tz,
        )
        detect_resp = await self.clients.detect(event=event, features=preprocess_resp.features)
        enriched_event = event.model_copy(update={"pattern_match_ids": detect_resp.matched_ids})
        signals = _to_signals(detect_resp.matches)
        score_resp = await self.clients.score(event=enriched_event, signals=signals)
        return IngestEventResponse(
            event_id=event.id,
            current_score=score_resp.current_score,
            tier=score_resp.tier,
            delta=score_resp.delta,
            signals=signals,
        )
