"""AABB overlap guards for routed wires vs waveform step polylines."""

from __future__ import annotations

from manim_engineering.components import Resistor
from manim_engineering.layout import LayoutEngine
from manim_engineering.layout.aabb import (
    aabb_overlap,
    segment_bbox,
    union_bbox,
    vertical_gap_above,
)
from manim_engineering.layout.routing import points_to_segments
from manim_engineering.layout.types import Segment
from manim_engineering.semantic import CircuitGraph, LogicLevel, LogicState, Signal, SignalType
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


def _wire_segments(layout) -> tuple[Segment, ...]:
    segments: list[Segment] = []
    for wire in layout.wires:
        segments.extend(wire.segments)
    return tuple(segments)


def _waveform_segments(layout, bundle) -> tuple[Segment, ...]:
    panel = panel_below_layout(layout, trace_count=len(bundle.traces))
    segments: list[Segment] = []
    for index, trace in enumerate(bundle.traces):
        segments.extend(points_to_segments(step_polyline(trace, panel, index)))
    return tuple(segments)


def test_wire_and_waveform_bands_separated_by_min_gap() -> None:
    layout, bundle = _clock_data_fixture()
    wire_boxes = tuple(segment_bbox(seg) for seg in _wire_segments(layout))
    wave_boxes = tuple(segment_bbox(seg) for seg in _waveform_segments(layout, bundle))
    wire_band = union_bbox(wire_boxes)
    wave_band = union_bbox(wave_boxes)
    assert wire_band is not None and wave_band is not None
    gap = vertical_gap_above(wave_band, wire_band)
    assert gap >= MIN_WAVEFORM_GAP


def test_wire_waveform_segment_pairs_no_overlap_or_vertical_gap() -> None:
    layout, bundle = _clock_data_fixture()
    wire_boxes = [segment_bbox(seg) for seg in _wire_segments(layout)]
    wave_boxes = [segment_bbox(seg) for seg in _waveform_segments(layout, bundle)]
    for wire_box in wire_boxes:
        for wave_box in wave_boxes:
            if not aabb_overlap(wire_box, wave_box):
                continue
            gap = vertical_gap_above(wave_box, wire_box)
            assert gap >= MIN_WAVEFORM_GAP, (
                "overlapping wire/waveform segment AABBs require vertical gap "
                f">= {MIN_WAVEFORM_GAP}, got {gap}"
            )
