"""Example smoke contracts for analog-first catalog and retained smoke scripts."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def _load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize(
    ("rel_path", "builder"),
    (
        ("examples/analog/01_rc_charge.py", "build_rc_charge_fixture"),
        ("examples/analog/02_diode_rectifier.py", "build_rectifier_fixture"),
        ("examples/analog/03_cmos_inverter.py", "build_inverter_fixture"),
        ("examples/analog/04_npn_amplifier.py", "build_npn_amplifier_fixture"),
        ("examples/analog/05_opamp_inverting.py", "build_opamp_inverting_fixture"),
        ("examples/analog/06_opamp_integrator.py", "build_opamp_integrator_fixture"),
        ("examples/analog/07_zener_regulator.py", "build_zener_regulator_fixture"),
        ("examples/analog/08_rlc_transient.py", "build_rlc_transient_fixture"),
        ("examples/analog/09_mos_four_types.py", "build_mos_four_types_fixture"),
    ),
)
def test_analog_fixture_builders(rel_path: str, builder: str) -> None:
    mod = _load_module(REPO / rel_path)
    fn = getattr(mod, builder)
    graph, elements, layout = fn()
    assert graph.nodes
    assert elements
    if builder == "build_mos_four_types_fixture":
        assert len(layout.placements) == 4
    else:
        assert layout.wires


def test_basic_graph_only_main_smoke() -> None:
    mod = _load_module(REPO / "examples/basics/graph_only.py")
    mod.main()


def test_protocol_spi_main_smoke() -> None:
    mod = _load_module(REPO / "examples/protocol/spi_byte_transfer.py")
    mod.main()


@pytest.mark.requires_manim
def test_protocol_spi_scene_class_available() -> None:
    pytest.importorskip("manim")
    from manim import Scene

    mod = _load_module(REPO / "examples/protocol/spi_byte_transfer.py")
    assert hasattr(mod, "SPIByteTransferDemo")
    assert issubclass(mod.SPIByteTransferDemo, Scene)
