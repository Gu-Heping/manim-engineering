"""Importable scene stand-in for animation orchestration tests."""

from __future__ import annotations


class RecordingScene:
    """Captures add/play/wait/remove calls without Manim rendering."""

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
