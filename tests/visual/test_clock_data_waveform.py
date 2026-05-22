"""Golden visual regression for examples/basics/clock_data_waveform.ClockDataWaveformDemo."""

from __future__ import annotations

import importlib.util
import os
import tempfile
from pathlib import Path

import pytest
from conftest import PHASH_HAMMING_TOLERANCE, requires_manim
from hashing import dhash_hex, hamming_hex, layout_waveform_geometry_digest

_GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
_GOLDEN_NAME = "clock_data_waveform.dhash.txt"
_EXAMPLE = (
    Path(__file__).resolve().parents[2] / "examples" / "basics" / "clock_data_waveform.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("clock_data_waveform", _EXAMPLE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _render_last_frame_png() -> Path:
    mod = _load_module()
    pytest.importorskip("manim")
    from manim import tempconfig

    tmpdir = tempfile.mkdtemp(prefix="me_visual_")
    with tempconfig(
        {
            "quality": "low_quality",
            "disable_caching": True,
            "media_dir": tmpdir,
            "write_to_movie": False,
            "save_last_frame": True,
        }
    ):
        mod.ClockDataWaveformDemo().render()

    matches = sorted(Path(tmpdir).rglob("ClockDataWaveformDemo*.png"))
    if not matches:
        raise FileNotFoundError(f"no ClockDataWaveformDemo PNG under {tmpdir}")
    return matches[-1]


def _geometry_hash_from_fixture() -> str:
    mod = _load_module()
    _graph, _elements, layout, _clock, _data, bundle = mod.build_fixture()
    return layout_waveform_geometry_digest(layout, bundle)


@requires_manim
def test_clock_data_waveform_last_frame_phash() -> None:
    """Last frame matches golden dHash (Hamming <= tolerance)."""
    png = _render_last_frame_png()
    actual = dhash_hex(png)
    golden_path = _GOLDEN_DIR / _GOLDEN_NAME

    if os.environ.get("UPDATE_VISUAL_GOLDEN"):
        golden_path.write_text(actual + "\n", encoding="utf-8")
        pytest.skip("golden updated via UPDATE_VISUAL_GOLDEN=1")

    expected = golden_path.read_text(encoding="utf-8").strip()
    distance = hamming_hex(actual, expected)
    assert distance <= PHASH_HAMMING_TOLERANCE, (
        f"dHash Hamming {distance} > {PHASH_HAMMING_TOLERANCE}: "
        f"actual={actual} expected={expected}. "
        "Re-run with UPDATE_VISUAL_GOLDEN=1 after intentional visual change."
    )


def test_clock_data_waveform_geometry_hash_recorded() -> None:
    """Point geometry hash is stable (layout + waveform panel)."""
    digest = _geometry_hash_from_fixture()
    geom_path = _GOLDEN_DIR / "clock_data_waveform.geometry.txt"

    if os.environ.get("UPDATE_VISUAL_GOLDEN"):
        geom_path.write_text(digest + "\n", encoding="utf-8")
        pytest.skip("geometry golden updated via UPDATE_VISUAL_GOLDEN=1")

    if not geom_path.exists():
        pytest.skip("geometry golden not committed yet; set UPDATE_VISUAL_GOLDEN=1 once")

    expected = geom_path.read_text(encoding="utf-8").strip()
    assert digest == expected
