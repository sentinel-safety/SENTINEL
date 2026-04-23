# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from pathlib import Path

import pytest

from shared.honeypot.personas import Persona, PersonaLoader, PersonaNotFoundError

pytestmark = pytest.mark.unit


def _write_persona(tmp_path: Path, name: str, body: str) -> None:
    (tmp_path / f"{name}.yaml").write_text(body, encoding="utf-8")


def test_persona_rejects_missing_consent_marker() -> None:
    with pytest.raises(ValueError, match="consent_statement"):
        Persona(
            id="x",
            age=13,
            gender="female",
            location="us-east",
            interests=("art",),
            vocabulary_level="age_typical",
            regional_speech="us_east_suburban",
            consent_statement="not correct",
            activation_scope=("US",),
            prompt_version="v1",
        )


def test_persona_rejects_invalid_age() -> None:
    with pytest.raises(ValueError):
        Persona(
            id="x",
            age=8,
            gender="female",
            location="us-east",
            interests=("art",),
            vocabulary_level="age_typical",
            regional_speech="us_east_suburban",
            consent_statement="SYNTHETIC — not a real child",
            activation_scope=("US",),
            prompt_version="v1",
        )


def test_persona_loader_reads_yaml(tmp_path: Path) -> None:
    _write_persona(
        tmp_path,
        "emma-13",
        """
id: emma-13-us-east
age: 13
gender: female
location: us-east
interests: [reading, roblox, art]
vocabulary_level: age_typical
regional_speech: us_east_suburban
consent_statement: "SYNTHETIC — not a real child"
activation_scope: [US]
prompt_version: v1
""".lstrip(),
    )
    loader = PersonaLoader(tmp_path)
    p = loader.get("emma-13-us-east")
    assert p.age == 13
    assert p.interests == ("reading", "roblox", "art")
    assert p.activation_scope == ("US",)


def test_persona_loader_missing_raises(tmp_path: Path) -> None:
    loader = PersonaLoader(tmp_path)
    with pytest.raises(PersonaNotFoundError):
        loader.get("does-not-exist")


def test_persona_loader_is_memoised(tmp_path: Path) -> None:
    _write_persona(
        tmp_path,
        "emma-13",
        """
id: emma-13-us-east
age: 13
gender: female
location: us-east
interests: [art]
vocabulary_level: age_typical
regional_speech: us_east_suburban
consent_statement: "SYNTHETIC — not a real child"
activation_scope: [US]
prompt_version: v1
""".lstrip(),
    )
    loader = PersonaLoader(tmp_path)
    a = loader.get("emma-13-us-east")
    b = loader.get("emma-13-us-east")
    assert a is b
