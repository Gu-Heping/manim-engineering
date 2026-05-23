"""Geometry golden for examples/protocol/uart_byte_transfer layout + waveforms."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest
from hashing import layout_waveform_geometry_digest

_GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
_EXAMPLE = (
    Path(__file__).resolve().parents[2] / "examples" / "protocol" / "uart_byte_transfer.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("uart_byte_transfer", _EXAMPLE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _geometry_hash_from_fixture() -> str:
    mod = _load_module()
    _graph, _elements, layout, _binding, _result, bundle = mod.build_uart_fixture()
    return layout_waveform_geometry_digest(layout, bundle)


def test_uart_byte_transfer_geometry_hash_recorded() -> None:
    """Point geometry hash is stable (layout + waveform panel, no raster)."""
    digest = _geometry_hash_from_fixture()
    geom_path = _GOLDEN_DIR / "uart_byte_transfer.geometry.txt"

    if os.environ.get("UPDATE_VISUAL_GOLDEN"):
        geom_path.write_text(digest + "\n", encoding="utf-8")
        pytest.skip("geometry golden updated via UPDATE_VISUAL_GOLDEN=1")

    if not geom_path.exists():
        pytest.skip("geometry golden not committed yet; set UPDATE_VISUAL_GOLDEN=1 once")

    expected = geom_path.read_text(encoding="utf-8").strip()
    assert digest == expected
