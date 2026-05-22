"""Waveform panel renderer structure tests."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim_engineering.components import Resistor
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import WaveformPanelRenderer
from manim_engineering.semantic import CircuitGraph, LogicLevel, LogicState, Signal, SignalType
from manim_engineering.waveform import derive_bundle_from_signals


def test_waveform_panel_renders_traces() -> None:
    graph = CircuitGraph()
    drv = Resistor("drv")
    rcv = Resistor("rcv")
    drv.attach_to(graph)
    rcv.attach_to(graph)
    graph.connect(drv.get_pin("b"), rcv.get_pin("a"))
    layout = LayoutEngine().layout(graph, {"drv": drv, "rcv": rcv})
    clock = Signal(name="clk", signal_type=SignalType.CLOCK, value=LogicState(level=LogicLevel.LOW))
    clock.propagate(drv.get_pin("b"), rcv.get_pin("a"), graph=graph)
    bundle = derive_bundle_from_signals((clock,))
    panel, spec = WaveformPanelRenderer().render_with_layout(bundle, layout)
    assert len(panel.submobjects) >= 2
    assert spec.width > 0
