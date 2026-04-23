# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from typing import Final
from uuid import UUID

from shared.schemas.base import FrozenModel
from shared.schemas.enums import Jurisdiction, ResponseTier
from shared.scoring.signals import ScoreSignal, SignalKind

MANDATORY_REPORT_TRIGGERING_SIGNALS: Final[frozenset[SignalKind]] = frozenset(
    {
        SignalKind.SEXUAL_ESCALATION,
        SignalKind.PHOTO_REQUEST,
        SignalKind.VIDEO_REQUEST,
        SignalKind.SECRECY_REQUEST,
    }
)

_TEMPLATE_BY_JURISDICTION: Final[dict[Jurisdiction, str]] = {
    Jurisdiction.US: "NCMEC_CYBERTIPLINE",
    Jurisdiction.UK: "NSPCC_IWF",
}


class MandatoryReportPackage(FrozenModel):
    tenant_id: UUID
    actor_id: UUID
    jurisdiction: Jurisdiction
    report_template: str
    triggering_signals: tuple[SignalKind, ...]
    evidence_bundle_url: str | None = None


def evaluate_mandatory_report(
    *,
    tenant_id: UUID,
    actor_id: UUID,
    tier: ResponseTier,
    jurisdictions: tuple[Jurisdiction, ...],
    signals: tuple[ScoreSignal, ...],
) -> MandatoryReportPackage | None:
    if tier != ResponseTier.CRITICAL:
        return None
    triggering = tuple(s.kind for s in signals if s.kind in MANDATORY_REPORT_TRIGGERING_SIGNALS)
    if not triggering:
        return None
    for jurisdiction in jurisdictions:
        template = _TEMPLATE_BY_JURISDICTION.get(jurisdiction)
        if template is None:
            continue
        return MandatoryReportPackage(
            tenant_id=tenant_id,
            actor_id=actor_id,
            jurisdiction=jurisdiction,
            report_template=template,
            triggering_signals=triggering,
        )
    return None
