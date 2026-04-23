from __future__ import annotations

from sentinel import __version__


def test_version_is_semver_like() -> None:
    parts = __version__.split(".")
    assert len(parts) == 3
    for part in parts:
        assert part.isdigit()
