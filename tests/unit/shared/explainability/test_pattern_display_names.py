# Copyright 2026 Sentinel Foundation. All Rights Reserved.
#
# Licensed under the SENTINEL License Agreement. See LICENSE file in the project
# root for full terms.


from __future__ import annotations

import pytest

from shared.explainability.pattern_display_names import PATTERN_DISPLAY_NAMES

pytestmark = pytest.mark.unit


def test_known_patterns_have_display_names() -> None:
    assert PATTERN_DISPLAY_NAMES["platform_migration"] == "Platform Migration Request"
    assert PATTERN_DISPLAY_NAMES["personal_info_probe"] == "Personal Information Probe"
    assert PATTERN_DISPLAY_NAMES["friendship_forming"] == "Friendship Forming Stage"
    assert PATTERN_DISPLAY_NAMES["sexual_escalation"] == "Sexual Escalation"
    assert PATTERN_DISPLAY_NAMES["sexual_escalation:photo_request"] == "Photo Request"
    assert PATTERN_DISPLAY_NAMES["sexual_escalation:video_request"] == "Video Request"


def test_display_names_are_title_case_strings() -> None:
    for slug, label in PATTERN_DISPLAY_NAMES.items():
        assert isinstance(slug, str)
        assert slug
        assert isinstance(label, str)
        assert label
        assert label[0].isupper()
