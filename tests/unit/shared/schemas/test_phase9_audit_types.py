# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.schemas.audit_log import AuditEventType
from shared.schemas.tenant import FeatureFlags

pytestmark = pytest.mark.unit


def test_honeypot_audit_event_types_registered() -> None:
    assert AuditEventType.HONEYPOT_ACTIVATED.value == "honeypot.activated"
    assert AuditEventType.HONEYPOT_DENIED.value == "honeypot.denied"
    assert AuditEventType.HONEYPOT_EVIDENCE_PACKAGED.value == "honeypot.evidence_packaged"


def test_feature_flags_has_legal_review_ack_default_false() -> None:
    flags = FeatureFlags()
    assert flags.honeypot_enabled is False
    assert flags.honeypot_legal_review_acknowledged is False
