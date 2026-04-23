# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field, field_validator

from shared.schemas.base import FrozenModel
from shared.schemas.enums import Jurisdiction

_REQUIRED_CONSENT_STATEMENT = "SYNTHETIC — not a real child"


class PersonaNotFoundError(FileNotFoundError):
    pass


class Persona(FrozenModel):
    id: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9\-]*$")
    age: int = Field(ge=9, le=17)
    gender: Literal["female", "male", "nonbinary"]
    location: str = Field(min_length=1, max_length=64)
    interests: tuple[str, ...] = Field(min_length=1, max_length=10)
    vocabulary_level: Literal["early_reader", "age_typical", "advanced_for_age"]
    regional_speech: str = Field(min_length=1, max_length=64)
    consent_statement: str
    activation_scope: tuple[Jurisdiction, ...] = Field(min_length=1)
    prompt_version: str = Field(default="v1", pattern=r"^v[0-9]+$")

    @field_validator("consent_statement")
    @classmethod
    def _require_synthetic_marker(cls, value: str) -> str:
        if value.strip() != _REQUIRED_CONSENT_STATEMENT:
            raise ValueError(f"consent_statement must be exactly {_REQUIRED_CONSENT_STATEMENT!r}")
        return value


class PersonaLoader:
    def __init__(self, personas_dir: Path) -> None:
        self._dir = Path(personas_dir)
        self._cache: dict[str, Persona] = {}

    def _load_all(self) -> None:
        for path in self._dir.glob("*.yaml"):
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
            persona = Persona.model_validate(payload)
            self._cache[persona.id] = persona

    def get(self, persona_id: str) -> Persona:
        if persona_id in self._cache:
            return self._cache[persona_id]
        self._load_all()
        if persona_id not in self._cache:
            raise PersonaNotFoundError(f"persona {persona_id!r} not found in {self._dir}")
        return self._cache[persona_id]

    def list_ids(self) -> tuple[str, ...]:
        self._load_all()
        return tuple(sorted(self._cache.keys()))
