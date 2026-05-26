"""RCChargeScene intro pipeline and teaching beat smoke tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("manim")

from manim import AnimationGroup, Create, LaggedStart, Scene

REPO = Path(__file__).resolve().parents[2]


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_rc_module():
    return _load_module(REPO / "examples/analog/01_rc_charge.py")


def _contains_create(animation: object) -> bool:
    if isinstance(animation, Create):
        return True
    if isinstance(animation, (LaggedStart, AnimationGroup)):
        return any(_contains_create(child) for child in animation.animations)
    return False


def test_rc_charge_scene_class_available() -> None:
    mod = _load_rc_module()
    assert hasattr(mod, "RCChargeScene")
    assert issubclass(mod.RCChargeScene, Scene)


def test_rc_teaching_beats_disable_wire_pulse() -> None:
    mod = _load_rc_module()
    _, _, _, signals, _, records = mod.build_rc_teaching_fixture()
    beats = mod._teaching_beats(signals, records)
    assert len(beats) == 2
    assert beats[0].wire_pulse is False
    assert beats[1].wire_pulse is False


def test_play_topology_intro_exported_from_animation_package() -> None:
    from manim_engineering.animation import CaptionTrack, play_hud_intro, play_topology_intro

    assert callable(play_topology_intro)
    assert callable(play_hud_intro)
    assert CaptionTrack is not None


def test_rc_shared_reexports_teaching_scene_from_package() -> None:
    shared = _load_module(REPO / "examples/_shared.py")
    assert shared.WaveformDemoScene.__module__.startswith("manim_engineering.animation")
    assert shared.WaveformFixture.__module__.startswith("manim_engineering.animation")
    assert shared.CaptionTrack.__module__.startswith("manim_engineering.animation")


def test_rc_charge_scene_construct_smoke() -> None:
    mod = _load_rc_module()

    class _RecordingScene(mod.RCChargeScene):
        def __init__(self) -> None:
            self.played: list[tuple[tuple[object, ...], dict]] = []
            self._waited = 0
            super().__init__()

        def play(self, *animations, **kwargs) -> None:
            self.played.append((animations, dict(kwargs)))

        def wait(self, duration: float = 0.0) -> None:
            del duration
            self._waited += 1

    scene = _RecordingScene()
    scene.construct()
    assert scene.played
    assert scene._waited > 0
    intro_anims, _ = scene.played[0]
    assert len(intro_anims) == 1
    assert _contains_create(intro_anims[0])


def test_waveform_demo_scene_lives_in_animation_package() -> None:
    from manim_engineering.animation import WaveformDemoScene

    assert WaveformDemoScene.__module__.endswith("teaching_scene")
