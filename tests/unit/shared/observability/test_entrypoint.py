# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.config import Settings
from shared.observability import configure_observability, get_logger, get_tracer

pytestmark = pytest.mark.unit


def test_configure_observability_sets_up_logging_and_tracing() -> None:
    configure_observability(Settings(env="test", log_level="INFO"))
    get_logger("t").info("ok")
    get_tracer("t").start_span("s").end()
