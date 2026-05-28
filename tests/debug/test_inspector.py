"""SceneInspector should reflect displayed scene content, including foreground."""

from __future__ import annotations

from manim_engineering.debug.inspector import SceneInspector


def test_scene_inspector_includes_foreground_mobjects() -> None:
    class _Mob:
        def __init__(self, name: str) -> None:
            self.name = name
            self.z_index = 0
            self.submobjects = []

        def get_bounding_box(self):
            return [
                [0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [1.0, 1.0, 0.0],
            ]

        def get_center(self):
            return [0.5, 0.5, 0.0]

    class _Scene:
        pass

    scene = _Scene()
    scene.mobjects = [_Mob("base")]
    scene.foreground_mobjects = [_Mob("foreground")]

    data = SceneInspector(scene).as_dict()

    assert len(data["objects"]) == 2
