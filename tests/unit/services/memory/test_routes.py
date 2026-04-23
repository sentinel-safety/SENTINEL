# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from services.memory.app.main import create_app
from shared.config import Settings

pytestmark = pytest.mark.unit


def test_memory_service_exposes_actor_memory_route() -> None:
    app = create_app(Settings(env="test"))
    paths = {r.path for r in app.routes if hasattr(r, "path")}
    assert "/internal/actor-memory" in paths
