"""SPIByteTransferDemo construct smoke tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytest.importorskip("manim")

from manim import AnimationGroup, Create, LaggedStart, Scene

REPO = Path(__file__).resolve().parents[2]


def _load_spi_module():
    spec = importlib.util.spec_from_file_location(
        "spi_byte_transfer",
        REPO / "examples/protocol/spi_byte_transfer.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _contains_create(animation: object) -> bool:
    if isinstance(animation, Create):
        return True
    if isinstance(animation, (LaggedStart, AnimationGroup)):
        return any(_contains_create(child) for child in animation.animations)
    return False


def test_spi_scene_class_available() -> None:
    mod = _load_spi_module()
    assert hasattr(mod, "SPIByteTransferDemo")
    assert issubclass(mod.SPIByteTransferDemo, Scene)


def test_spi_scene_construct_smoke() -> None:
    mod = _load_spi_module()

    class _RecordingScene(mod.SPIByteTransferDemo):
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
