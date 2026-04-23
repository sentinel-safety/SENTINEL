# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import Iterator

import pytest

from shared.observability import clear_context, reset_observability


@pytest.fixture(autouse=True)
def _reset_observability() -> Iterator[None]:
    reset_observability()
    clear_context()
    yield
    reset_observability()
    clear_context()
