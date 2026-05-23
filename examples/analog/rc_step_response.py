"""
R + NMOS (as switch) + C step-response topology — Scope A symbol layout.

Replaces the previous R1↔C1 minimal smoke with a more realistic teaching
shape: a digital edge driving an NMOS gate "closes the switch", which then
lets current flow R → drain → source → C. The semantic model is still
discrete (digital edge); continuous RC dynamics remain ROADMAP backlog
(Scope B/C — see docs/ROADMAP.md "Analog symbol set (Scope A)").

Topology
--------

.. code::

    step ──► NMOS.gate
              │
              ▼
    R.b ────► NMOS.drain
              │
              ▼
    NMOS.source ────► C.a

Smoke: ``python examples/analog/rc_step_response.py``

NMOS acts as a switch; analog dynamics still digital edge — see ROADMAP
backlog for continuous physics.

Layout uses :data:`RC_STEP_OVERRIDES` so R.b aligns with the drain (top
edge) and the channel is not crossed by a horizontal segment at gate height
(see ``examples/analog/README.md``).
"""

from __future__ import annotations

from manim_engineering.components import NMOS, Capacitor, InputDriver, Resistor
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import LayoutEngine, Point2D
from manim_engineering.semantic import LogicLevel, LogicState, Signal

# Bottom-left origins (world units). Tuned so R.b and NMOS.drain share y=1.0.
RC_STEP_OVERRIDES: dict[str, Point2D] = {
    "step_drv": Point2D(-1.35, 0.55),
    "r1": Point2D(0.0, 0.875),
    "m1": Point2D(1.5, 0.0),
    "c1": Point2D(3.2, 0.0),
}


def build_fixture():
    """Return circuit, elements, layout after step-edge + switch-on propagation.

    Propagations recorded into history:

    1. ``step`` (DIGITAL) drives the NMOS gate (LOW→HIGH).
    2. ``vrail`` (ANALOG) is conducted from R.b through NMOS to C.a.
    """
    circuit = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    m1 = NMOS("m1", label="M1")
    c1 = Capacitor("c1", label="C1")
    step_drv = InputDriver("step_drv", label="STEP", signal_type=SignalType.DIGITAL)
    circuit.add(r1)
    circuit.add(m1)
    circuit.add(c1)
    circuit.add(step_drv)

    circuit.connect(step_drv.get_pin("out"), m1.get_pin("gate"))
    circuit.connect(r1.port_b, m1.get_pin("drain"))
    circuit.connect(m1.get_pin("source"), c1.port_a)

    elements = {"r1": r1, "m1": m1, "c1": c1, "step_drv": step_drv}
    layout = LayoutEngine().layout(
        circuit,
        elements,
        placement_overrides=RC_STEP_OVERRIDES,
    )

    gate_step = Signal(
        name="step",
        signal_type=SignalType.DIGITAL,
        value=LogicState(level=LogicLevel.LOW),
    )
    gate_step.propagate(step_drv.get_pin("out"), m1.get_pin("gate"), graph=circuit)
    gate_step.value = LogicState(level=LogicLevel.HIGH)
    gate_step.propagate(step_drv.get_pin("out"), m1.get_pin("gate"), graph=circuit)

    vrail = Signal(
        name="vrail",
        signal_type=SignalType.ANALOG,
        value=LogicState(level=LogicLevel.LOW),
    )
    vrail.propagate(r1.port_b, m1.get_pin("drain"), graph=circuit)
    vrail.propagate(m1.get_pin("source"), c1.port_a, graph=circuit)
    return circuit, elements, layout


def main() -> None:
    circuit, _elements, layout = build_fixture()
    print(f"nodes: {len(circuit.nodes)}, connections: {len(circuit.connections)}")
    print(f"layout occupancy: {layout.occupancy_ratio:.1%}")
    for placement in layout.placements:
        print(
            f"{placement.element_id}: origin=({placement.origin.x:.3f}, {placement.origin.y:.3f})"
        )


if __name__ == "__main__":
    main()
