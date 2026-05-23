"""Wire vs component footprint regression tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from manim_engineering.layout import assert_wires_avoid_footprints

_EXAMPLES = Path(__file__).resolve().parents[2] / "examples"


def _load_fixture(rel: str, func: str = "build_clock_data_fixture"):
    path = _EXAMPLES / rel
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, func)()


def test_clock_data_wires_avoid_resistor_footprints() -> None:
    _graph, _elements, layout, *_rest = _load_fixture(
        "basics/clock_data_waveform.py",
        "build_clock_data_fixture",
    )
    assert_wires_avoid_footprints(layout)


def test_rc_step_response_wires_avoid_footprints() -> None:
    _circuit, _elements, layout = _load_fixture(
        "analog/rc_step_response.py",
        "build_fixture",
    )
    assert_wires_avoid_footprints(layout)


def test_governance_acceptance_wires_avoid_footprints() -> None:
    _circuit, _elements, layout, *_rest = _load_fixture(
        "basics/governance_acceptance.py",
        "build_fixture",
    )
    assert_wires_avoid_footprints(layout)


def test_spi_byte_transfer_wires_avoid_footprints() -> None:
    _graph, _elements, layout, *_rest = _load_fixture(
        "protocol/spi_byte_transfer.py",
        "build_spi_fixture",
    )
    assert_wires_avoid_footprints(layout)


def test_uart_byte_transfer_wires_avoid_footprints() -> None:
    _graph, _elements, layout, *_rest = _load_fixture(
        "protocol/uart_byte_transfer.py",
        "build_uart_fixture",
    )
    assert_wires_avoid_footprints(layout)


def test_uart_tx_left_of_rx() -> None:
    _graph, _elements, layout, *_rest = _load_fixture(
        "protocol/uart_byte_transfer.py",
        "build_uart_fixture",
    )
    tx = next(p for p in layout.placements if p.element_id == "tx_dev")
    rx = next(p for p in layout.placements if p.element_id == "rx_dev")
    assert tx.origin.x < rx.origin.x


def test_spi_fixture_four_routed_wires() -> None:
    _graph, _elements, layout, *_rest = _load_fixture(
        "protocol/spi_byte_transfer.py",
        "build_spi_fixture",
    )
    assert len(layout.wires) == 4
