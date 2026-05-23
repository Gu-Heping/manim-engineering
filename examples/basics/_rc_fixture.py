"""Shared R–C edge fixture: InputDriver → R1 → C1 → Ground (teaching topology)."""

from __future__ import annotations

from manim_engineering.components import Capacitor, Ground, InputDriver, Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine
from manim_engineering.layout.types import LayoutResult
from manim_engineering.semantic import LogicLevel, LogicState, Signal
from manim_engineering.semantic.teaching_edges import record_rising_edge
from manim_engineering.waveform import derive_bundle_from_signals
from manim_engineering.waveform.trace import WaveformBundle


def build_rc_edge_fixture() -> tuple[
    CircuitGraph,
    dict[str, object],
    LayoutResult,
    Signal,
    WaveformBundle,
]:
    """Minimal closed RC path with two propagation beats (plate charge + return path).

    Scope A: ``edge`` is a **digital teaching trace**, not a continuous RC exponential.
    """
    circuit = CircuitGraph()
    in_drv = InputDriver("in_drv", label="IN")
    r1 = Resistor("r1", label="R1")
    c1 = Capacitor("c1", label="C1")
    gnd = Ground("gnd1", label="GND")
    for comp in (in_drv, r1, c1, gnd):
        comp.attach_to(circuit)

    circuit.connect(in_drv.get_pin("out"), r1.get_pin("a"))
    circuit.connect(r1.get_pin("b"), c1.get_pin("a"))
    circuit.connect(c1.get_pin("b"), gnd.get_pin("gnd"))

    elements = {"in_drv": in_drv, "r1": r1, "c1": c1, "gnd1": gnd}
    layout = LayoutEngine().layout(circuit, elements)

    edge = Signal(
        name="edge",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    record_rising_edge(edge, r1.get_pin("b"), c1.get_pin("a"), graph=circuit)
    record_rising_edge(edge, c1.get_pin("b"), gnd.get_pin("gnd"), graph=circuit)
    bundle = derive_bundle_from_signals((edge,))
    return circuit, elements, layout, edge, bundle
