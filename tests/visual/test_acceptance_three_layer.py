"""Golden visual regression for examples/basics/acceptance_three_layer.AcceptanceScene."""

from __future__ import annotations

import importlib.util
import os
import tempfile
from pathlib import Path

import pytest
from conftest import PHASH_HAMMING_TOLERANCE, requires_manim
from hashing import dhash_hex, hamming_hex, stable_geometry_hash_lines_only

_GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
_GOLDEN_NAME = "acceptance_three_layer.dhash.txt"
_EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "basics" / "acceptance_three_layer.py"


def _load_acceptance_module():
    spec = importlib.util.spec_from_file_location("acceptance_three_layer", _EXAMPLE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _render_last_frame_png() -> Path:
    mod = _load_acceptance_module()
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
        mod.AcceptanceScene().render()

    matches = sorted(Path(tmpdir).rglob("AcceptanceScene*.png"))
    if not matches:
        raise FileNotFoundError(f"no AcceptanceScene PNG under {tmpdir}")
    return matches[-1]


def _geometry_hash_from_fixture() -> str:
    """Stable point-geometry digest when scene raster is unavailable."""
    mod = _load_acceptance_module()
    pytest.importorskip("manim")
    from manim_engineering.renderers.minimal import ManimRenderer

    circuit, elements, layout, _signal = mod.build_fixture()
    mob = ManimRenderer().render(circuit, layout, elements)
    return stable_geometry_hash_lines_only(mob)


@requires_manim
def test_acceptance_three_layer_last_frame_phash() -> None:
    """Last frame of AcceptanceScene matches golden dHash (Hamming <= tolerance)."""
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


@requires_manim
def test_acceptance_three_layer_geometry_hash_recorded() -> None:
    """Point geometry hash is stable (guards layout/render without full raster)."""
    digest = _geometry_hash_from_fixture()
    geom_path = _GOLDEN_DIR / "acceptance_three_layer.geometry.txt"

    if os.environ.get("UPDATE_VISUAL_GOLDEN"):
        geom_path.write_text(digest + "\n", encoding="utf-8")
        pytest.skip("geometry golden updated via UPDATE_VISUAL_GOLDEN=1")

    if not geom_path.exists():
        pytest.skip("geometry golden not committed yet; set UPDATE_VISUAL_GOLDEN=1 once")

    expected = geom_path.read_text(encoding="utf-8").strip()
    assert digest == expected
