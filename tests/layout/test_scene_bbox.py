"""Scene bbox union and waveform panel separation below routed wires."""

from __future__ import annotations

from manim_engineering.components import Resistor
from manim_engineering.layout import LayoutEngine, scene_bbox
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.semantic import LogicLevel, LogicState, Signal
from manim_engineering.waveform import (
    MIN_WAVEFORM_GAP,
    derive_bundle_from_signals,
    panel_below_layout,
    step_polyline,
)


def _clock_data_fixture():
    graph = CircuitGraph()
    drv = Resistor("drv", label="DRV")
    rcv = Resistor("rcv", label="RCV")
    drv.attach_to(graph)
    rcv.attach_to(graph)
    graph.connect(drv.get_pin("b"), rcv.get_pin("a"))
    graph.connect(drv.get_pin("a"), rcv.get_pin("b"))
    elements = {"drv": drv, "rcv": rcv}
    layout = LayoutEngine().layout(graph, elements)
    clock = Signal(name="clk", signal_type=SignalType.CLOCK, value=LogicState(level=LogicLevel.LOW))
    data = Signal(name="data", signal_type=SignalType.DATA, value=LogicState(level=LogicLevel.LOW))
    clock.propagate(drv.get_pin("b"), rcv.get_pin("a"), graph=graph)
    data.propagate(drv.get_pin("a"), rcv.get_pin("b"), graph=graph)
    bundle = derive_bundle_from_signals((clock, data))
    return layout, bundle


def test_scene_bbox_covers_wire_points() -> None:
    layout, _ = _clock_data_fixture()
    computed = scene_bbox(layout.placements, layout.wires)
    assert layout.scene_bbox == computed
    wire_ys = [point.y for wire in layout.wires for point in wire.points]
    assert layout.scene_bbox.min_y <= min(wire_ys)
    assert layout.scene_bbox.max_y >= max(wire_ys)


def test_waveform_panel_separated_below_wires() -> None:
    layout, bundle = _clock_data_fixture()
    panel = panel_below_layout(layout, trace_count=len(bundle.traces))
    max_wire_y = max(point.y for wire in layout.wires for point in wire.points)
    assert max_wire_y - panel.origin.y >= MIN_WAVEFORM_GAP
    panel_top = panel.origin.y + panel.panel_height(len(bundle.traces))
    assert layout.scene_bbox.min_y - panel_top >= MIN_WAVEFORM_GAP


def test_waveform_step_polylines_below_routed_wires() -> None:
    """In world Y-up coords: lowest wire point sits MIN_WAVEFORM_GAP above waveform band."""
    layout, bundle = _clock_data_fixture()
    panel = panel_below_layout(layout, trace_count=len(bundle.traces))
    min_wire_y = min(point.y for wire in layout.wires for point in wire.points)
    polyline_ys: list[float] = []
    for index, trace in enumerate(bundle.traces):
        for pt in step_polyline(trace, panel, index):
            polyline_ys.append(pt.y)
    assert polyline_ys
    max_polyline_y = max(polyline_ys)
    assert min_wire_y - max_polyline_y >= MIN_WAVEFORM_GAP
