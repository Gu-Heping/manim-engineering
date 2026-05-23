"""Aspect invariants: rendered output must match the configured pixel aspect.

These tests render only the first frame (cheap) for canonical scenes and
verify the framing helper produced a logical frame whose aspect matches
the pixel aspect — so dots stay round and text stays unsquashed.
"""

from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

import pytest
from conftest import requires_manim


def _example(rel: str) -> Path:
    return Path(__file__).resolve().parents[2] / "examples" / rel


_SCENES: tuple[tuple[str, Path, str], ...] = (
    ("clock_data_waveform", _example("basics/clock_data_waveform.py"), "ClockDataWaveformDemo"),
    ("uart_byte_transfer", _example("protocol/uart_byte_transfer.py"), "UARTByteTransferDemo"),
    ("spi_byte_transfer", _example("protocol/spi_byte_transfer.py"), "SPIByteTransferDemo"),
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@requires_manim
@pytest.mark.parametrize("name,path,scene_cls", _SCENES, ids=lambda x: x if isinstance(x, str) else "")
def test_scene_camera_matches_pixel_aspect(name: str, path: Path, scene_cls: str) -> None:
    """After ``construct`` runs, scene.camera frame aspect == pixel aspect."""
    pytest.importorskip("manim")
    from manim import config, tempconfig

    mod = _load(name, path)
    cls = getattr(mod, scene_cls)

    with tempfile.TemporaryDirectory(prefix=f"me_aspect_{name}_") as tmp:
        with tempconfig(
            {
                "quality": "low_quality",
                "disable_caching": True,
                "media_dir": tmp,
                "write_to_movie": False,
                "save_last_frame": True,
            }
        ):
            scene = cls()
            scene.render()
            camera = scene.camera
            target = config.pixel_width / config.pixel_height
            actual = float(camera.frame_width) / float(camera.frame_height)
            assert actual == pytest.approx(target, rel=1e-3), (
                f"{name}: camera aspect {actual:.4f} != pixel aspect {target:.4f}"
            )
