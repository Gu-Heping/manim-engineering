"""Structural typing for Manim-like teaching scenes."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class TeachingSceneProtocol(Protocol):
    """Minimal scene surface used by animation orchestration helpers."""

    def add(self, *mobjects: object) -> None: ...

    def play(self, *animations: object, run_time: float | None = None) -> None: ...

    def wait(self, duration: float = 0.0) -> None: ...

    def remove(self, *mobjects: object) -> None: ...

    @property
    def camera(self) -> Any: ...


def require_scene_methods(
    scene: object,
    *,
    require_play: bool = True,
    require_add: bool = False,
    require_wait: bool = False,
    require_remove: bool = False,
) -> TeachingSceneProtocol:
    """Validate ``scene`` exposes orchestration methods; raise ``TypeError`` early."""
    missing: list[str] = []
    if require_add and not callable(getattr(scene, "add", None)):
        missing.append("add()")
    if require_play and not callable(getattr(scene, "play", None)):
        missing.append("play()")
    if require_wait and not callable(getattr(scene, "wait", None)):
        missing.append("wait()")
    if require_remove and not callable(getattr(scene, "remove", None)):
        missing.append("remove()")
    if missing:
        msg = f"scene must provide {' and '.join(missing)} like manim.Scene"
        raise TypeError(msg)
    return scene  # type: ignore[return-value]
