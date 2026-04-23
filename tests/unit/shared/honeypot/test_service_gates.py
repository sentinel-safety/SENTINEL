# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import re
from pathlib import Path

import pytest

from shared.honeypot.activation import ActivationDecision
from shared.honeypot.service import HoneypotContext, HoneypotDenied, HoneypotResult, invoke_honeypot

pytestmark = pytest.mark.unit


class _StubProvider:
    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.calls = 0

    async def complete(self, *, prompt: str, schema: object) -> dict[str, object]:
        self.calls += 1
        return {"reply": self.reply}


async def test_invoke_returns_denied_when_gate_fails(tmp_path: Path) -> None:
    (tmp_path / "emma.yaml").write_text(
        "id: emma\nage: 13\ngender: female\nlocation: us-east\n"
        "interests: [art]\nvocabulary_level: age_typical\nregional_speech: us_east_suburban\n"
        'consent_statement: "SYNTHETIC — not a real child"\n'
        "activation_scope: [US]\nprompt_version: v1\n",
        encoding="utf-8",
    )
    from shared.honeypot.personas import PersonaLoader

    provider = _StubProvider("hi")
    ctx = HoneypotContext(
        actor_tier=0,
        tenant_feature_flags={
            "honeypot_enabled": False,
            "honeypot_legal_review_acknowledged": False,
        },
        tenant_jurisdictions=(),
        jurisdiction_allowlist=(),
        persona_id="emma",
        persona_loader=PersonaLoader(tmp_path),
        conversation_excerpt=(),
        provider=provider,
        tier_threshold=4,
    )
    result = await invoke_honeypot(ctx)
    assert isinstance(result, HoneypotDenied)
    assert result.decision.allowed is False
    assert provider.calls == 0


async def test_invoke_returns_result_when_all_gates_pass(tmp_path: Path) -> None:
    (tmp_path / "emma.yaml").write_text(
        "id: emma\nage: 13\ngender: female\nlocation: us-east\n"
        "interests: [art]\nvocabulary_level: age_typical\nregional_speech: us_east_suburban\n"
        'consent_statement: "SYNTHETIC — not a real child"\n'
        "activation_scope: [US]\nprompt_version: v1\n",
        encoding="utf-8",
    )
    from shared.honeypot.personas import PersonaLoader
    from shared.schemas.enums import Jurisdiction

    provider = _StubProvider("hey")
    ctx = HoneypotContext(
        actor_tier=4,
        tenant_feature_flags={"honeypot_enabled": True, "honeypot_legal_review_acknowledged": True},
        tenant_jurisdictions=(Jurisdiction.US,),
        jurisdiction_allowlist=(Jurisdiction.US,),
        persona_id="emma",
        persona_loader=PersonaLoader(tmp_path),
        conversation_excerpt=("actor: hi",),
        provider=provider,
        tier_threshold=4,
    )
    result = await invoke_honeypot(ctx)
    assert isinstance(result, HoneypotResult)
    assert result.reply == "hey"
    assert result.decision == ActivationDecision(allowed=True, reasons=())
    assert provider.calls == 1


def test_no_other_entrypoints_reach_prompt_or_evidence() -> None:
    allowed_roots = {
        Path("shared/honeypot/service.py").resolve(),
        Path("shared/honeypot/prompt.py").resolve(),
        Path("shared/honeypot/evidence.py").resolve(),
        Path("shared/honeypot/__init__.py").resolve(),
        Path("shared/honeypot/personas.py").resolve(),
        Path("shared/honeypot/activation.py").resolve(),
        Path("shared/honeypot/repository.py").resolve(),
    }
    pattern = re.compile(r"from\s+shared\.honeypot\.(prompt|evidence)\s+import")
    offenders: list[Path] = []
    for root in (Path("services"), Path("shared")):
        for py in root.rglob("*.py"):
            if py.resolve() in allowed_roots:
                continue
            text = py.read_text(encoding="utf-8")
            if pattern.search(text):
                offenders.append(py)
    assert offenders == [], (
        f"direct imports of shared.honeypot.prompt/evidence are forbidden outside the service "
        f"entrypoint — offenders: {offenders}"
    )
