from __future__ import annotations

from manim_engineering import build_circuit, layout_circuit
from manim_engineering.components import Capacitor, Ground, Resistor


def test_layout_circuit_reports_clean_small_chain() -> None:
    result = build_circuit(
        {
            "r1": Resistor("r1"),
            "r2": Resistor("r2"),
        },
        [("r1", "b", "r2", "a")],
    )

    outcome = layout_circuit(result)

    assert outcome.layout_mode == "semantic_grid"
    assert outcome.warnings == ()
    assert outcome.needs_attention is False


def test_layout_circuit_warns_when_auto_grid_exceeds_occupancy_target() -> None:
    elements = {f"r{i}": Resistor(f"r{i}") for i in range(8)}
    connections = [(f"r{i}", "b", f"r{i+1}", "a") for i in range(7)]

    result = build_circuit(elements, connections)
    outcome = layout_circuit(result)

    assert "layout.occupancy_above_target" in outcome.warnings
    assert "layout.single_row_auto_grid" in outcome.warnings
    assert outcome.needs_attention is True


def test_layout_circuit_uses_structured_auto_for_branching_topology() -> None:
    result = build_circuit(
        {
            "r1": Resistor("r1"),
            "r2": Resistor("r2"),
            "r3": Resistor("r3"),
            "c1": Capacitor("c1"),
            "gnd": Ground("gnd"),
        },
        [
            ("r1", "b", "r2", "a"),
            ("r2", "b", "r3", "a"),
            ("r2", "b", "c1", "a"),
            ("c1", "b", "gnd", "gnd"),
        ],
    )

    outcome = layout_circuit(result)

    assert outcome.layout_mode == "structured_auto"
    ys = {
        round(placement.origin.y, 6)
        for placement in outcome.layout.placements
    }
    assert len(ys) > 1
    assert "layout.branching_topology_using_auto_grid" not in outcome.warnings
