"""Geometry golden for examples/analog/rc_step_response layout (no raster)."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest
from hashing import layout_geometry_digest

_GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
_EXAMPLE = (
    Path(__file__).resolve().parents[2] / "examples" / "analog" / "rc_step_response.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("rc_step_response", _EXAMPLE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_rc_step_response_import_and_solve() -> None:
    """Smoke: R + NMOS + C + InputDriver; three routed nets including gate."""
    mod = _load_module()
    circuit, elements, layout = mod.build_fixture()
    assert len(circuit.nodes) == 4
    assert len(layout.wires) == 3
    assert "r1" in elements and "m1" in elements and "c1" in elements


def test_rc_step_response_geometry_hash_recorded() -> None:
    """Layout-only geometry digest is stable (placements + wires, no raster)."""
    mod = _load_module()
    _circuit, _elements, layout = mod.build_fixture()
    digest = layout_geometry_digest(layout)
    geom_path = _GOLDEN_DIR / "rc_step_response.geometry.txt"

    if os.environ.get("UPDATE_VISUAL_GOLDEN"):
        geom_path.write_text(digest + "\n", encoding="utf-8")
        pytest.skip("geometry golden updated via UPDATE_VISUAL_GOLDEN=1")

    if not geom_path.exists():
        pytest.skip("geometry golden not committed yet; set UPDATE_VISUAL_GOLDEN=1 once")

    expected = geom_path.read_text(encoding="utf-8").strip()
    assert digest == expected
