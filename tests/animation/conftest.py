"""Shared fixtures for animation tests."""

from __future__ import annotations

import pytest
from recording_scene import RecordingScene

try:
    import manim  # noqa: F401

    HAS_MANIM = True
except ImportError:
    HAS_MANIM = False

requires_manim = pytest.mark.skipif(
    not HAS_MANIM,
    reason="manim not installed (pip install -e '.[manim]')",
)


@pytest.fixture
def recording_scene() -> RecordingScene:
    return RecordingScene()
