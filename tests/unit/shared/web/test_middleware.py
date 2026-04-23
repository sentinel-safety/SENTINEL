# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

from uuid import UUID

import pytest

from shared.web.middleware import coerce_request_id

pytestmark = pytest.mark.unit


def test_coerce_request_id_generates_uuid_when_absent() -> None:
    UUID(coerce_request_id(None))


def test_coerce_request_id_preserves_valid_uuid() -> None:
    valid = "01234567-89ab-cdef-0123-456789abcdef"
    assert coerce_request_id(valid) == valid


def test_coerce_request_id_replaces_invalid_input() -> None:
    result = coerce_request_id("not-a-uuid")
    assert result != "not-a-uuid"
    UUID(result)
