"""Snapshot helpers should redraw the current scene state before capture."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from manim_engineering.debug import snapshot as snapshot_mod


def test_snapshot_frame_updates_renderer_before_capture(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("ME_ANIMATION_SNAPSHOT", "1")
    monkeypatch.setattr(snapshot_mod, "DEBUG_OUTPUT_DIR", tmp_path)

    image = MagicMock()
    camera = SimpleNamespace(get_image=MagicMock(return_value=image))
    renderer = SimpleNamespace(update_frame=MagicMock(), static_image=object())
    class ProbeScene:
        pass

    scene = ProbeScene()
    scene.camera = camera
    scene.renderer = renderer

    path = snapshot_mod.snapshot_frame(scene, "after_hud")

    assert path == tmp_path / "ProbeScene" / "after_hud.png"
    renderer.update_frame.assert_called_once_with(scene, mobjects=[])
    assert renderer.static_image is not None
    image.save.assert_called_once_with(str(path))


def test_snapshot_frame_clears_static_image_during_redraw(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("ME_ANIMATION_SNAPSHOT", "1")
    monkeypatch.setattr(snapshot_mod, "DEBUG_OUTPUT_DIR", tmp_path)

    observed_static: list[object | None] = []
    image = MagicMock()
    camera = SimpleNamespace(get_image=MagicMock(return_value=image))

    def _update_frame(_scene, *, mobjects) -> None:
        observed_static.append(renderer.static_image)
        assert mobjects == []

    renderer = SimpleNamespace(update_frame=_update_frame, static_image=object())

    class ProbeScene:
        pass

    scene = ProbeScene()
    scene.camera = camera
    scene.renderer = renderer

    snapshot_mod.snapshot_frame(scene, "after_intro")

    assert observed_static == [None]
    assert renderer.static_image is not None


def test_redraw_scene_frame_uses_displayed_mobjects() -> None:
    renderer = MagicMock()

    class ProbeScene:
        pass

    scene = ProbeScene()
    scene.renderer = renderer
    scene.mobjects = [object()]
    scene.foreground_mobjects = [object()]

    snapshot_mod.redraw_scene_frame(scene)

    renderer.update_frame.assert_called_once_with(
        scene,
        mobjects=scene.mobjects + scene.foreground_mobjects,
    )


def test_snapshot_topology_includes_foreground_mobjects(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("ME_ANIMATION_SNAPSHOT", "1")
    monkeypatch.setattr(snapshot_mod, "DEBUG_OUTPUT_DIR", tmp_path)

    class _Mob:
        def __init__(self, x0: float, y0: float, x1: float, y1: float) -> None:
            self.z_index = 0
            self._bbox = [
                [x0, y0, 0.0],
                [x0, y1, 0.0],
                [x1, y1, 0.0],
            ]

        def get_bounding_box(self):
            return self._bbox

    class ProbeScene:
        pass

    scene = ProbeScene()
    scene.mobjects = [_Mob(0.0, 0.0, 1.0, 1.0)]
    scene.foreground_mobjects = [_Mob(2.0, 2.0, 3.0, 3.0)]

    dump = snapshot_mod.snapshot_topology(scene, "after_hud")

    assert dump is not None
    assert len(dump["objects"]) == 2
