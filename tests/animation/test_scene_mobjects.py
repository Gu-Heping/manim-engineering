"""Scene displayed-mobject helpers used by static background refresh."""

from __future__ import annotations

from manim_engineering.animation.scene_mobjects import scene_display_mobjects
from manim_engineering.animation.teaching_scene import _refresh_static_scene_background


def test_scene_display_mobjects_includes_foreground_mobjects() -> None:
    class _Scene:
        pass

    scene = _Scene()
    a = object()
    b = object()
    c = object()
    scene.mobjects = [a, b]
    scene.foreground_mobjects = [c]

    assert scene_display_mobjects(scene) == [a, b, c]


def test_refresh_static_scene_background_uses_display_mobjects() -> None:
    class _Renderer:
        def __init__(self) -> None:
            self.calls: list[tuple[object, list[object]]] = []

        def save_static_frame_data(self, scene_obj, static_mobjects) -> None:
            self.calls.append((scene_obj, list(static_mobjects)))

    class _Scene:
        pass

    scene = _Scene()
    a = object()
    b = object()
    c = object()
    scene.renderer = _Renderer()
    scene.mobjects = [a, b]
    scene.foreground_mobjects = [c]

    _refresh_static_scene_background(scene)

    assert scene.renderer.calls == [(scene, [a, b, c])]
