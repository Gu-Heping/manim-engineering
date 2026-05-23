"""clock_data_waveform fixture: dual nets and four explicit edges."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from manim_engineering.semantic.enums import LogicLevel

_EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "basics" / "clock_data_waveform.py"


def _load():
    spec = importlib.util.spec_from_file_location("clock_data_waveform_example", _EXAMPLE)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_clock_and_data_use_separate_connections() -> None:
    graph, _elements, _layout, clk, data, _bundle = _load().build_clock_data_fixture()
    assert len(graph.connections) == 2
    pin_pairs = {
        frozenset((c.port_a.id, c.port_b.id)) for c in graph.connections
    }
    assert frozenset(("drv.b", "rcv.a")) in pin_pairs
    assert frozenset(("drv.a", "rcv.b")) in pin_pairs
    assert len(clk.propagation_history) == 2
    assert len(data.propagation_history) == 2
    assert clk.propagation_history[1].new_value.level == LogicLevel.LOW
    assert data.propagation_history[1].new_value.level == LogicLevel.LOW
