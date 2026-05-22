"""
RC passive chain: graph, layout, and one semantic edge (no SPICE).

Minimal analog smoke — reuses Resistor/Capacitor only; illustrates layout.solve
and optional propagation along the routed net (digital edge as stand-in for step).

Smoke: ``python examples/analog/rc_step_response.py``
"""

from __future__ import annotations

from manim_engineering.components import Capacitor, Resistor
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine
from manim_engineering.semantic import LogicLevel, LogicState, Signal, SignalType


def build_fixture():
    """Return circuit, elements, layout after one propagate along R1→C1."""
    circuit = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    c1 = Capacitor("c1", label="C1")
    circuit.add(r1)
    circuit.add(c1)
    circuit.connect(r1.port_b, c1.port_a)

    elements = {"r1": r1, "c1": c1}
    layout = LayoutEngine().solve(circuit, elements)

    edge = Signal(
        name="step",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    edge.propagate(r1.port_b, c1.port_a, graph=circuit)
    return circuit, elements, layout


def main() -> None:
    circuit, _elements, layout = build_fixture()
    print(f"nodes: {len(circuit.nodes)}, connections: {len(circuit.connections)}")
    print(f"layout occupancy: {layout.occupancy_ratio:.1%}")
    for placement in layout.placements:
        print(
            f"{placement.element_id}: "
            f"origin=({placement.origin.x:.3f}, {placement.origin.y:.3f})"
        )


if __name__ == "__main__":
    main()
