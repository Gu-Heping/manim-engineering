from __future__ import annotations

from manim_engineering import build_circuit, layout_circuit
from manim_engineering.components import (
    VCC,
    Capacitor,
    Ground,
    InputDriver,
    Resistor,
)
from manim_engineering.core import SignalType
from manim_engineering.layout import Point2D


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
    assert outcome.routing_report == outcome.layout.routing_report
    assert outcome.warnings == ()
    assert outcome.needs_attention is False
    assert outcome.recommended_action == "accept"


def test_layout_circuit_warns_when_auto_grid_exceeds_occupancy_target() -> None:
    elements = {f"r{i}": Resistor(f"r{i}") for i in range(8)}
    connections = [(f"r{i}", "b", f"r{i+1}", "a") for i in range(7)]

    result = build_circuit(elements, connections)
    outcome = layout_circuit(result)

    assert "layout.occupancy_above_target" in outcome.warnings
    assert "layout.single_row_auto_grid" in outcome.warnings
    assert outcome.needs_attention is True
    assert outcome.recommended_action == "use_preset_or_overrides"


def test_layout_circuit_surfaces_crossing_attention_warnings() -> None:
    result = build_circuit(
        {
            "r1": Resistor("r1"),
            "r2": Resistor("r2"),
            "vcc": VCC("vcc"),
            "gnd": Ground("gnd"),
        },
        [
            ("r1", "b", "r2", "a"),
            ("vcc", "vcc", "gnd", "gnd"),
        ],
    )

    outcome = layout_circuit(
        result,
        placement_overrides={
            "r1": Point2D(0.0, 0.0),
            "r2": Point2D(2.0, 0.0),
            "vcc": Point2D(1.4, -1.2),
            "gnd": Point2D(1.4, 1.0),
        },
    )

    assert "layout.routing_crossing_without_junction" in outcome.warnings
    assert outcome.routing_report.has_attention_items is True
    assert outcome.recommended_action == "review_routing"


def test_layout_circuit_surfaces_wire_through_component_warning() -> None:
    build = build_circuit(
        {
            "r1": Resistor("r1", label="R1"),
            "r2": Resistor("r2", label="R2"),
            "r3": Resistor("r3", label="R3"),
        },
        [("r1", "b", "r3", "a")],
    )

    outcome = layout_circuit(
        build,
        placement_overrides={
            "r1": Point2D(0.0, 0.0),
            "r2": Point2D(1.0, -0.1),
            "r3": Point2D(2.0, 0.0),
        },
    )

    assert "layout.routing_wire_through_component" not in outcome.warnings
    assert outcome.routing_report.detoured_path_count >= 1
    assert not any(
        issue.kind == "wire_through_component"
        for issue in outcome.routing_report.issues
    )
    assert outcome.recommended_action == "review_routing"


def test_layout_circuit_surfaces_wire_near_unconnected_pin_warning() -> None:
    build = build_circuit(
        {
            "r1": Resistor("r1", label="R1"),
            "r2": Resistor("r2", label="R2"),
            "gnd": Ground("gnd", label="GND"),
        },
        [("r1", "b", "r2", "a")],
    )

    outcome = layout_circuit(
        build,
        placement_overrides={
            "r1": Point2D(0.0, 0.0),
            "r2": Point2D(0.5, 0.02),
            "gnd": Point2D(0.55, -0.2),
        },
    )

    assert "layout.routing_wire_near_unconnected_pin" not in outcome.warnings
    assert outcome.routing_report.detoured_path_count >= 1
    assert not any(
        issue.kind == "wire_near_unconnected_pin"
        for issue in outcome.routing_report.issues
    )
    assert outcome.recommended_action == "accept"


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
    assert outcome.recommended_action == "review_routing"


def test_layout_circuit_treats_empty_overrides_as_auto_layout() -> None:
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

    outcome = layout_circuit(result, placement_overrides={})

    assert outcome.layout_mode == "structured_auto"
    assert "layout.branching_topology_using_auto_grid" not in outcome.warnings
    assert outcome.recommended_action == "review_routing"


def test_layout_circuit_detects_fanout_branching_topology() -> None:
    result = build_circuit(
        {
            "vin": InputDriver("vin", signal_type=SignalType.ANALOG),
            "r1": Resistor("r1"),
            "c1": Capacitor("c1"),
        },
        [
            ("vin", "out", "r1", "a"),
            ("vin", "out", "c1", "a"),
        ],
    )

    outcome = layout_circuit(result)

    assert outcome.layout_mode == "structured_auto"
    assert "layout.branching_topology_using_auto_grid" not in outcome.warnings
    assert outcome.recommended_action == "review_routing"
