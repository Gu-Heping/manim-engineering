"""Construct smoke for topology-only analog teaching scenes."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("manim")

from manim import AnimationGroup, Create, DrawBorderThenFill, LaggedStart, Scene

REPO = Path(__file__).resolve().parents[2]


def _load_module(rel_path: str):
    path = REPO / rel_path
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _contains_intro_reveal(animation: object) -> bool:
    if isinstance(animation, (Create, DrawBorderThenFill)):
        return True
    if isinstance(animation, (LaggedStart, AnimationGroup)):
        return any(_contains_intro_reveal(child) for child in animation.animations)
    return False


@pytest.mark.parametrize(
    ("rel_path", "scene_name"),
    (
        ("examples/analog/02_diode_rectifier.py", "HalfWaveRectifierScene"),
        ("examples/analog/04_npn_amplifier.py", "NPNAmplifierScene"),
        ("examples/analog/05_opamp_inverting.py", "OpAmpInvertingScene"),
        ("examples/analog/06_opamp_integrator.py", "OpAmpIntegratorScene"),
        ("examples/analog/07_zener_regulator.py", "ZenerRegulatorScene"),
        ("examples/analog/08_rlc_transient.py", "RLCTransientScene"),
        ("examples/analog/09_mos_four_types.py", "MosFourTypesScene"),
        ("examples/analog/09_mos_four_types.py", "MosFourTypesArrowOnChannelScene"),
    ),
)
def test_topology_analog_scene_construct_smoke(rel_path: str, scene_name: str) -> None:
    mod = _load_module(rel_path)
    scene_cls = getattr(mod, scene_name)
    assert scene_cls is not None
    assert issubclass(scene_cls, Scene)

    class _RecordingScene(scene_cls):
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
    assert any(_contains_intro_reveal(anim) for anim in intro_anims)
