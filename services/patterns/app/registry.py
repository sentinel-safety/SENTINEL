# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from services.patterns.app.library.age_incongruence import AgeIncongruencePattern
from services.patterns.app.library.behavioral_fingerprint_match import (
    BehavioralFingerprintMatchPattern,
)
from services.patterns.app.library.cross_session_escalation import (
    CrossSessionEscalationPattern,
)
from services.patterns.app.library.desensitization import DesensitizationPattern
from services.patterns.app.library.exclusivity import ExclusivityPattern
from services.patterns.app.library.exclusivity_llm import ExclusivityLLMPattern
from services.patterns.app.library.friendship_forming import FriendshipFormingPattern
from services.patterns.app.library.gift_offering import GiftOfferingPattern
from services.patterns.app.library.isolation import IsolationPattern
from services.patterns.app.library.late_night import LateNightPattern
from services.patterns.app.library.multi_minor_contact import MultiMinorContactPattern
from services.patterns.app.library.personal_info_probe import PersonalInfoProbePattern
from services.patterns.app.library.platform_migration import PlatformMigrationPattern
from services.patterns.app.library.risk_assessment import RiskAssessmentPattern
from services.patterns.app.library.secrecy_request import SecrecyRequestPattern
from services.patterns.app.library.sexual_escalation import SexualEscalationPattern
from services.patterns.app.library.suspicious_cluster_membership import (
    SuspiciousClusterMembershipPattern,
)
from shared.config.settings import get_settings
from shared.llm.factory import build_llm_provider
from shared.llm.provider import LLMProvider
from shared.patterns import LLMPattern, Pattern

_llm_provider = build_llm_provider(get_settings())

SYNC_PATTERNS: tuple[Pattern, ...] = (
    SecrecyRequestPattern(),
    PlatformMigrationPattern(),
    PersonalInfoProbePattern(),
    GiftOfferingPattern(),
    ExclusivityPattern(),
    LateNightPattern(),
    MultiMinorContactPattern(),
    CrossSessionEscalationPattern(),
    AgeIncongruencePattern(),
    BehavioralFingerprintMatchPattern(),
    SuspiciousClusterMembershipPattern(),
)
LLM_PATTERNS: tuple[LLMPattern, ...] = (
    FriendshipFormingPattern(provider=_llm_provider),
    RiskAssessmentPattern(provider=_llm_provider),
    IsolationPattern(provider=_llm_provider),
    DesensitizationPattern(provider=_llm_provider),
    SexualEscalationPattern(provider=_llm_provider),
    ExclusivityLLMPattern(provider=_llm_provider),
)


def build_llm_patterns(provider: LLMProvider) -> tuple[LLMPattern, ...]:
    return (
        FriendshipFormingPattern(provider=provider),
        RiskAssessmentPattern(provider=provider),
        IsolationPattern(provider=provider),
        DesensitizationPattern(provider=provider),
        SexualEscalationPattern(provider=provider),
        ExclusivityLLMPattern(provider=provider),
    )
