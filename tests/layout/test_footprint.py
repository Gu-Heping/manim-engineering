"""Wire vs component footprint checks for analog fixtures."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from manim_engineering.layout.footprint import assert_wires_avoid_footprints

REPO = Path(__file__).resolve().parents[2]


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize(
    "rel_path, builder",
    (
        ("examples/analog/03_cmos_inverter.py", "build_inverter_fixture"),
        ("examples/analog/04_npn_amplifier.py", "build_npn_amplifier_fixture"),
        ("examples/analog/05_opamp_inverting.py", "build_opamp_inverting_fixture"),
        ("examples/analog/06_opamp_integrator.py", "build_opamp_integrator_fixture"),
        ("examples/analog/07_zener_regulator.py", "build_zener_regulator_fixture"),
    ),
)
def test_analog_fixture_wires_avoid_footprints(rel_path: str, builder: str) -> None:
    mod = _load_module(REPO / rel_path)
    _graph, _elements, layout = getattr(mod, builder)()
    assert_wires_avoid_footprints(layout)
