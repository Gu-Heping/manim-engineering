"""Geometry golden for examples/protocol/spi_byte_transfer layout + waveforms."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from conftest import assert_or_update_golden_text
from hashing import layout_waveform_geometry_digest

_GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
_EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "protocol" / "spi_byte_transfer.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("spi_byte_transfer", _EXAMPLE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _geometry_hash_from_fixture() -> str:
    mod = _load_module()
    _graph, _elements, layout, _binding, _result, bundle = mod.build_spi_fixture()
    return layout_waveform_geometry_digest(layout, bundle)


def test_spi_byte_transfer_geometry_hash_recorded() -> None:
    """Point geometry hash is stable (layout + waveform panel, no raster)."""
    digest = _geometry_hash_from_fixture()
    geom_path = _GOLDEN_DIR / "spi_byte_transfer.geometry.txt"
    assert_or_update_golden_text(geom_path, digest, label="spi_byte_transfer geometry")
