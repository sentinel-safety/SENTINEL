# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from shared.synthetic.axes import GroomingStage

STAGE_PROMPTS: dict[GroomingStage, str] = {
    GroomingStage.FRIENDSHIP_FORMING: (
        "Generate a short chat conversation where an adult builds initial rapport with a younger "
        "person, using compliments and shared interests. Use surface-level pattern cues only "
        "(e.g. 'you seem really mature', 'I feel like we have so much in common'). "
        "Stage: friendship_forming."
    ),
    GroomingStage.RISK_ASSESSMENT: (
        "Generate a short chat conversation where an adult subtly probes a younger person's home "
        "situation, parental supervision, and online habits. Surface cues only "
        "(e.g. 'do your parents check your phone?', 'are you home alone a lot?'). "
        "Stage: risk_assessment."
    ),
    GroomingStage.EXCLUSIVITY: (
        "Generate a short chat conversation where an adult creates a sense of special connection "
        "and exclusivity with a younger person. Surface cues only "
        "(e.g. 'you are so mature for your age', 'I feel like only you understand me'). "
        "Stage: exclusivity."
    ),
    GroomingStage.ISOLATION: (
        "Generate a short chat conversation where an adult encourages a younger person to keep "
        "their relationship secret and distance from friends/family. Surface cues only "
        "(e.g. 'don't tell your parents', 'your friends wouldn\\'t understand us'). "
        "Stage: isolation."
    ),
    GroomingStage.DESENSITIZATION: (
        "Generate a short chat conversation where an adult gradually introduces boundary-testing "
        "topics with a younger person. Surface cues only "
        "(e.g. 'have you ever kissed anyone?', 'let\\'s play a dare game'). "
        "Stage: desensitization."
    ),
    GroomingStage.SEXUAL_ESCALATION: (
        "Generate a short chat conversation showing early sexual escalation signals between an "
        "adult and a younger person. Use ONLY safe placeholder phrases — no explicit content "
        "(e.g. 'can you send me a pic?', 'lets move to telegram where it\\'s more private'). "
        "Stage: sexual_escalation."
    ),
}
