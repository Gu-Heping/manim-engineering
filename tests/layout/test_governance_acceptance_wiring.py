"""Governance R1–C1 fixture: wire endpoints must match pin world positions."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_PIN_EPSILON = 1e-6

_EXAMPLE = (
    Path(__file__).resolve().parents[2] / "examples" / "basics" / "governance_acceptance.py"
)


def _load_fixture():
    spec = importlib.util.spec_from_file_location("governance_acceptance", _EXAMPLE)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_fixture()


def test_governance_wire_endpoints_at_pins() -> None:
    _circuit, elements, layout, _edge, _bundle = _load_fixture()

    for wire in layout.wires:
        start_pin = wire.points[0]
        end_pin = wire.points[-1]
        assert any(
            abs(start_pin.x - pos.x) < _PIN_EPSILON and abs(start_pin.y - pos.y) < _PIN_EPSILON
            for pos in layout.pin_positions.values()
        )
        assert any(
            abs(end_pin.x - pos.x) < _PIN_EPSILON and abs(end_pin.y - pos.y) < _PIN_EPSILON
            for pos in layout.pin_positions.values()
        )
        assert start_pin in layout.pin_positions.values()
        assert end_pin in layout.pin_positions.values()


def test_governance_inter_component_wire_in_gap() -> None:
    """Net between R1 and C1 must not run through either component footprint."""
    _circuit, elements, layout, _edge, _bundle = _load_fixture()
    assert len(layout.wires) == 1
    wire = layout.wires[0]
    r1 = next(p for p in layout.placements if p.element_id == "r1")
    c1 = next(p for p in layout.placements if p.element_id == "c1")
    gap_x0 = r1.origin.x + r1.bounds.width
    gap_x1 = c1.origin.x

    for segment in wire.segments:
        if segment.start.y == segment.end.y:
            y = segment.start.y
            x_min = min(segment.start.x, segment.end.x)
            x_max = max(segment.start.x, segment.end.x)
            if x_min >= gap_x0 and x_max <= gap_x1:
                assert r1.origin.y <= y <= r1.origin.y + r1.bounds.height
                continue
        if segment.start.x == segment.end.x:
            x = segment.start.x
            assert gap_x0 <= x <= gap_x1 or x in (gap_x0, gap_x1)
