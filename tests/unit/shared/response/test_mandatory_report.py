# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import uuid4

import pytest

from shared.response.mandatory_report import (
    MANDATORY_REPORT_TRIGGERING_SIGNALS,
    evaluate_mandatory_report,
)
from shared.schemas.enums import Jurisdiction, ResponseTier
from shared.scoring.signals import ScoreSignal, SignalKind

pytestmark = pytest.mark.unit


def _signal(kind: SignalKind) -> ScoreSignal:
    return ScoreSignal(kind=kind, confidence=0.9, evidence="ev")


def test_us_critical_with_sexual_escalation_fires() -> None:
    pkg = evaluate_mandatory_report(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        tier=ResponseTier.CRITICAL,
        jurisdictions=(Jurisdiction.US,),
        signals=(_signal(SignalKind.SEXUAL_ESCALATION),),
    )
    assert pkg is not None
    assert pkg.report_template == "NCMEC_CYBERTIPLINE"


def test_uk_critical_with_photo_request_fires() -> None:
    pkg = evaluate_mandatory_report(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        tier=ResponseTier.CRITICAL,
        jurisdictions=(Jurisdiction.UK,),
        signals=(_signal(SignalKind.PHOTO_REQUEST),),
    )
    assert pkg is not None
    assert pkg.report_template == "NSPCC_IWF"


def test_non_critical_does_not_fire() -> None:
    pkg = evaluate_mandatory_report(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        tier=ResponseTier.RESTRICT,
        jurisdictions=(Jurisdiction.US,),
        signals=(_signal(SignalKind.SEXUAL_ESCALATION),),
    )
    assert pkg is None


def test_critical_without_triggering_signal_does_not_fire() -> None:
    pkg = evaluate_mandatory_report(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        tier=ResponseTier.CRITICAL,
        jurisdictions=(Jurisdiction.US,),
        signals=(_signal(SignalKind.FRIENDSHIP_FORMING),),
    )
    assert pkg is None


def test_critical_with_non_reporting_jurisdiction_does_not_fire() -> None:
    pkg = evaluate_mandatory_report(
        tenant_id=uuid4(),
        actor_id=uuid4(),
        tier=ResponseTier.CRITICAL,
        jurisdictions=(Jurisdiction.EU,),
        signals=(_signal(SignalKind.SEXUAL_ESCALATION),),
    )
    assert pkg is None


def test_triggering_set_includes_expected_kinds() -> None:
    assert SignalKind.SEXUAL_ESCALATION in MANDATORY_REPORT_TRIGGERING_SIGNALS
    assert SignalKind.PHOTO_REQUEST in MANDATORY_REPORT_TRIGGERING_SIGNALS
    assert SignalKind.VIDEO_REQUEST in MANDATORY_REPORT_TRIGGERING_SIGNALS
    assert SignalKind.SECRECY_REQUEST in MANDATORY_REPORT_TRIGGERING_SIGNALS
    assert SignalKind.FRIENDSHIP_FORMING not in MANDATORY_REPORT_TRIGGERING_SIGNALS
