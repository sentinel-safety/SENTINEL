# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import random
from datetime import UTC, datetime
from uuid import UUID, uuid4

from shared.llm.provider import LLMProvider
from shared.synthetic.axes import (
    DiversityAxes,
    GroomingStage,
    StageMix,
)
from shared.synthetic.dataset import SyntheticConversation, SyntheticDataset, SyntheticTurn
from shared.synthetic.stages import STAGE_PROMPTS

FORBIDDEN_TOKENS: frozenset[str] = frozenset(
    {
        "nude",
        "nudes",
        "naked",
        "underage",
        "child porn",
        "cp",
        "loli",
        "lolita",
        "shota",
        "jailbait",
        "pedo",
        "pedophile",
        "pedophilia",
        "csam",
        "child sexual",
        "sexual abuse material",
        "explicit photo",
        "explicit image",
        "send pics",
        "dick pic",
        "cock",
        "pussy",
        "vagina",
        "penis",
        "fuck",
        "fucking",
        "sex me",
        "have sex",
        "rape",
        "molest",
        "coordinates",
        "lat lon",
        "gps location",
        "meet me at",
        "come to my house",
        "my address",
    }
)

SAFE_FALLBACKS: dict[GroomingStage, str] = {
    GroomingStage.FRIENDSHIP_FORMING: "you seem really cool, we have a lot in common",
    GroomingStage.RISK_ASSESSMENT: "do your parents usually check your phone?",
    GroomingStage.EXCLUSIVITY: "you are so mature for your age, i feel like only you get me",
    GroomingStage.ISOLATION: "don't tell your parents, they wouldn't understand",
    GroomingStage.DESENSITIZATION: "have you ever kissed anyone before?",
    GroomingStage.SEXUAL_ESCALATION: "can you send me a pic? let's move to telegram",
}


def contains_forbidden_content(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in FORBIDDEN_TOKENS)


def _pick_stage(rng: random.Random, mix: StageMix) -> GroomingStage:
    stages = list(mix.weights.keys())
    weights = [mix.weights[s] for s in stages]
    return rng.choices(stages, weights=weights, k=1)[0]


def _pick_from(rng: random.Random, items: tuple[object, ...]) -> object:
    return rng.choice(list(items))


async def _generate_turn_text(
    prompt: str,
    provider: LLMProvider,
    stage: GroomingStage,
) -> str:
    for attempt in range(3):
        suffix = (
            " Strict content policy applies — output safe pattern-detectable cues only."
            if attempt > 0
            else ""
        )
        try:
            result = await provider.complete(
                prompt=prompt + suffix,
                schema={
                    "type": "object",
                    "properties": {"text": {"type": "string"}},
                    "required": ["text"],
                },
            )
            text = str(result.get("text", ""))
        except Exception:
            text = ""
        if not contains_forbidden_content(text) and text:
            return text
    return SAFE_FALLBACKS[stage]


async def generate_dataset(
    *,
    axes: DiversityAxes,
    stage_mix: StageMix,
    count: int,
    seed: int,
    provider: LLMProvider,
    run_id: UUID | None = None,
) -> SyntheticDataset:
    rng = random.Random(seed)  # noqa: S311
    effective_run_id = run_id or uuid4()
    conversations: list[SyntheticConversation] = []

    for _ in range(count):
        stage = _pick_stage(rng, stage_mix)
        demo = _pick_from(rng, axes.demographics)
        platform = _pick_from(rng, axes.platforms)
        style = _pick_from(rng, axes.communication_styles)
        language = _pick_from(rng, axes.languages)
        turn_count = rng.randint(3, 12)
        base_prompt = STAGE_PROMPTS[stage]
        turns: list[SyntheticTurn] = []
        offset = 0
        for i in range(turn_count):
            role = "actor" if i % 2 == 0 else "target"
            text = await _generate_turn_text(base_prompt, provider, stage)
            turns.append(
                SyntheticTurn(role=role, text=text[:2000], timestamp_offset_seconds=offset)
            )
            offset += rng.randint(10, 120)

        conversations.append(
            SyntheticConversation.model_validate(
                {
                    "id": uuid4(),
                    "stage": stage,
                    "demographics": demo,
                    "platform": platform,
                    "communication_style": style,
                    "language": str(language),
                    "turns": turns,
                }
            )
        )

    return SyntheticDataset(
        run_id=effective_run_id,
        seed=seed,
        axes=axes,
        stage_mix=stage_mix,
        conversations=tuple(conversations),
        generated_at=datetime.now(UTC),
        schema_version=1,
    )
