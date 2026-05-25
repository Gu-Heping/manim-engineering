"""Shared fixtures for animation tests."""

from __future__ import annotations

import pytest

try:
    import manim  # noqa: F401

    HAS_MANIM = True
except ImportError:
    HAS_MANIM = False

requires_manim = pytest.mark.skipif(
    not HAS_MANIM,
    reason="manim not installed (pip install -e '.[manim]')",
)


class RecordingScene:
    """Scene stand-in: captures add/play/wait/remove calls."""

    def __init__(self) -> None:
        self.added: list[object] = []
        self.played: list[tuple[object, ...]] = []
        self.run_times: list[float | None] = []
        self.waited: list[float] = []
        self.removed: list[object] = []

    def add(self, *mobjects: object) -> None:
        self.added.extend(mobjects)

    def play(self, *animations: object, run_time: float | None = None) -> None:
        self.played.append(animations)
        self.run_times.append(run_time)

    def wait(self, duration: float = 0.0) -> None:
        self.waited.append(duration)

    def remove(self, *mobjects: object) -> None:
        self.removed.extend(mobjects)

