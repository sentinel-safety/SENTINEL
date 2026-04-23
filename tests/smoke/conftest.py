# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from collections.abc import Iterator

import pytest

from shared.observability import reset_observability


@pytest.fixture(autouse=True)
def _reset_observability_between_tests() -> Iterator[None]:
    reset_observability()
    yield
    reset_observability()
