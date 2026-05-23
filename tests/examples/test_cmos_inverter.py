"""CMOS inverter example structure tests (topology + canonical vertical stack)."""

from __future__ import annotations

from examples.analog.cmos_inverter import (
    INVERTER_OVERRIDES,
    OUT_LABEL_WORLD,
    build_inverter_fixture,
)


def test_topology_node_and_connection_count() -> None:
    """Five nodes (VCC, PMOS, NMOS, GND, InputDriver) and five wires (no placeholder)."""
    graph, elements, _layout, _signals = build_inverter_fixture()
    assert len(graph.nodes) == 5
    assert len(graph.connections) == 5
    assert set(elements) == {"vcc1", "pm1", "nm1", "gnd1", "in_drv"}


def test_no_placeholder_resistors_in_topology() -> None:
    """Regression: the old layout used ``Resistor("in_src")`` / ``Resistor("out_net")``
    as fanout placeholders; the rewritten topology must not reintroduce them."""
    _graph, elements, _layout, _signals = build_inverter_fixture()
    assert "in_src" not in elements
    assert "out_net" not in elements


def test_vertical_stack_y_order() -> None:
    """VCC.y > PMOS.y > NMOS.y > GND.y and in_drv.x < PMOS.x (canonical inverter)."""
    _graph, _elements, layout, _signals = build_inverter_fixture()
    by_id = {p.element_id: p for p in layout.placements}
    assert by_id["vcc1"].origin.y > by_id["pm1"].origin.y
    assert by_id["pm1"].origin.y > by_id["nm1"].origin.y
    assert by_id["nm1"].origin.y > by_id["gnd1"].origin.y
    assert by_id["in_drv"].origin.x < by_id["pm1"].origin.x


def test_pin_positions_match_canonical_column() -> None:
    """All four rail/transistor right-side pins share the same x (single bus)."""
    _graph, _elements, layout, _signals = build_inverter_fixture()
    vcc_pin = layout.pin_positions["vcc1.vcc"]
    pm_source = layout.pin_positions["pm1.source"]
    pm_drain = layout.pin_positions["pm1.drain"]
    nm_drain = layout.pin_positions["nm1.drain"]
    nm_source = layout.pin_positions["nm1.source"]
    gnd_pin = layout.pin_positions["gnd1.gnd"]
    column_x = pm_source.x
    assert vcc_pin.x == column_x
    assert pm_drain.x == column_x
    assert nm_drain.x == column_x
    assert nm_source.x == column_x
    assert gnd_pin.x == column_x


def test_vcc_pin_meets_pmos_source_without_crossing_symbol() -> None:
    """VCC anchor at bottom meets PMOS source at the same junction (no wire through VCC body)."""
    _graph, _elements, layout, _signals = build_inverter_fixture()
    vcc_pin = layout.pin_positions["vcc1.vcc"]
    pm_source = layout.pin_positions["pm1.source"]
    assert vcc_pin.x == pm_source.x
    assert vcc_pin.y == pm_source.y


def test_nmos_source_meets_gnd_pin() -> None:
    """GND anchor at top meets NMOS source at the same junction."""
    _graph, _elements, layout, _signals = build_inverter_fixture()
    nm_source = layout.pin_positions["nm1.source"]
    gnd_pin = layout.pin_positions["gnd1.gnd"]
    assert nm_source.x == gnd_pin.x
    assert nm_source.y == gnd_pin.y


def test_pmos_drain_above_nmos_drain() -> None:
    """The OUT net (drain-drain wire) runs vertically with PMOS above NMOS."""
    _graph, _elements, layout, _signals = build_inverter_fixture()
    pm_drain = layout.pin_positions["pm1.drain"]
    nm_drain = layout.pin_positions["nm1.drain"]
    assert pm_drain.y > nm_drain.y
    assert pm_drain.x == nm_drain.x


def test_out_label_world_position_between_drains() -> None:
    """``OUT_LABEL_WORLD`` sits between the two drain pins vertically and to the right."""
    _graph, _elements, layout, _signals = build_inverter_fixture()
    pm_drain = layout.pin_positions["pm1.drain"]
    nm_drain = layout.pin_positions["nm1.drain"]
    label_x, label_y = OUT_LABEL_WORLD
    assert nm_drain.y < label_y < pm_drain.y
    assert label_x > pm_drain.x


def test_input_driver_fans_out_to_both_gates() -> None:
    """``in_drv.out`` must connect to both PMOS.gate and NMOS.gate."""
    graph, _elements, _layout, _signals = build_inverter_fixture()
    connections = [(c.port_a.id, c.port_b.id) for c in graph.connections]
    assert ("in_drv.out", "pm1.gate") in connections
    assert ("in_drv.out", "nm1.gate") in connections


def test_main_propagation_history_records_four_beats() -> None:
    """IN gate + OUT pull paths: two edges on IN, two on OUT."""
    _graph, _elements, _layout, signals = build_inverter_fixture()
    in_history = signals["in_sig"].propagation_history
    out_history = signals["out_sig"].propagation_history
    assert len(in_history) == 2
    assert len(out_history) == 2
    assert in_history[0].from_pin_id == "in_drv.out"
    assert in_history[0].to_pin_id == "nm1.gate"
    assert in_history[1].from_pin_id == "in_drv.out"
    from manim_engineering.semantic.enums import LogicLevel

    assert in_history[1].new_value.level == LogicLevel.LOW
    assert out_history[0].from_pin_id == "pm1.drain"
    assert out_history[0].to_pin_id == "nm1.drain"
    assert out_history[1].from_pin_id == "pm1.drain"
    assert out_history[1].to_pin_id == "nm1.drain"


def test_overrides_constant_covers_every_element() -> None:
    """Plan invariant: INVERTER_OVERRIDES must pin every element id."""
    _graph, elements, _layout, _signals = build_inverter_fixture()
    assert set(INVERTER_OVERRIDES) == set(elements)
