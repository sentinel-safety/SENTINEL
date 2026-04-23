# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from typing import Any, Final

from jinja2 import Environment, StrictUndefined

_ENV: Final[Environment] = Environment(
    undefined=StrictUndefined,
    autoescape=False,  # noqa: S701  # nosec B701 — evidence strings render to plain text, never HTML
    keep_trailing_newline=False,
)

EVIDENCE_TEMPLATES: Final[dict[str, str]] = {
    "secrecy_request": 'Actor requested secrecy in this message: "{{ matched_phrase }}".',
    "platform_migration": 'Actor asked to move the conversation off-platform: "{{ matched_phrase }}".',
    "personal_info_probe": 'Actor probed the minor for personal information: "{{ matched_phrase }}".',
    "gift_offering": 'Actor offered money or gifts to the minor: "{{ matched_phrase }}".',
    "exclusivity": 'Actor used exclusivity language with the minor: "{{ matched_phrase }}".',
    "exclusivity_llm": 'Language model flagged exclusivity framing with confidence {{ confidence }}: "{{ excerpt }}".',
    "late_night": "Actor contacted a minor during late-night local hours.",
    "multi_minor_contact": "Actor contacted {{ distinct_minors }} distinct minors in the last {{ lookback_days }} days ({{ velocity_per_day }} per day).",
    "cross_session_escalation": "Actor messaged minors across {{ conversations }} conversations with {{ distinct_targets }} distinct minor targets in the recent window.",
    "age_incongruence": "Actor's claimed age band is inconsistent with observed behaviour.",
    "behavioral_fingerprint_match": "Actor's behavioural fingerprint matched a known flagged actor (similarity {{ similarity }}).",
    "suspicious_cluster_membership": "Actor clusters with {{ flagged_neighbors }} flagged actors above the {{ threshold }} similarity threshold.",
    "friendship_forming": 'Language model flagged friendship-forming stage cues with confidence {{ confidence }}: "{{ excerpt }}".',
    "risk_assessment": 'Language model flagged risk-assessment probing with confidence {{ confidence }}: "{{ excerpt }}".',
    "isolation": 'Language model flagged isolation attempts with confidence {{ confidence }}: "{{ excerpt }}".',
    "desensitization": 'Language model flagged desensitization cues with confidence {{ confidence }}: "{{ excerpt }}".',
    "sexual_escalation": 'Language model flagged sexual escalation with confidence {{ confidence }}: "{{ excerpt }}".',
    "sexual_escalation:photo_request": 'Actor requested a photo during sexual-escalation cues (confidence {{ confidence }}): "{{ excerpt }}".',
    "sexual_escalation:video_request": 'Actor requested a video during sexual-escalation cues (confidence {{ confidence }}): "{{ excerpt }}".',
    "federation_signal_match": "Federated fingerprint match from publisher {{ publisher_tenant_id }} (similarity {{ similarity }}, reputation {{ reputation }}).",
}


class MissingTemplateError(KeyError):
    pass


def render_evidence(*, pattern_name: str, variables: dict[str, Any]) -> str:
    if pattern_name not in EVIDENCE_TEMPLATES:
        raise MissingTemplateError(pattern_name)
    template = _ENV.from_string(EVIDENCE_TEMPLATES[pattern_name])
    return template.render(**variables).strip()
