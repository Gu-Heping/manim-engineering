"""Layout stress fixture: multi-passive grid, occupancy, wire AABB, replay hash."""

from __future__ import annotations

import hashlib

import numpy as np

from manim_engineering.components import Capacitor, Resistor
from manim_engineering.components.types import Bounds
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import (
    OCCUPANCY_TARGET_MAX,
    OCCUPANCY_TARGET_MIN,
    LayoutConfig,
    LayoutEngine,
)
from manim_engineering.layout.aabb import aabb_overlap, segment_bbox
from manim_engineering.layout.types import DEFAULT_NOMINAL_FRAME

# Five-passive chain: widened nominal frame targets 60–75% (see place_on_grid span).
_STRESS_NOMINAL = Bounds(width=8.0, height=0.55)
_STRESS_OCCUPANCY_MIN = 0.60
_STRESS_OCCUPANCY_MAX = 0.75


def _five_passive_chain_fixture():
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    c1 = Capacitor("c1", label="C1")
    r2 = Resistor("r2", label="R2")
    c2 = Capacitor("c2", label="C2")
    r3 = Resistor("r3", label="R3")
    for element in (r1, c1, r2, c2, r3):
        element.attach_to(graph)
    graph.connect(r1.get_pin("b"), c1.get_pin("a"))
    graph.connect(c1.get_pin("b"), r2.get_pin("a"))
    graph.connect(r2.get_pin("b"), c2.get_pin("a"))
    graph.connect(c2.get_pin("b"), r3.get_pin("a"))
    elements = {
        "r1": r1,
        "c1": c1,
        "r2": r2,
        "c2": c2,
        "r3": r3,
    }
    config = LayoutConfig(nominal_frame=_STRESS_NOMINAL)
    layout = LayoutEngine(config).layout(graph, elements)
    return graph, elements, layout


def _wire_replay_digest(layout) -> str:
    parts: list[float] = []
    for wire in sorted(layout.wires, key=lambda w: w.connection_id):
        for pt in wire.points:
            parts.extend([pt.x, pt.y])
    rounded = np.round(np.asarray(parts, dtype=np.float64), decimals=4)
    return hashlib.sha256(rounded.tobytes()).hexdigest()


def test_layout_stress_occupancy_in_documented_band() -> None:
    _graph, _elements, layout = _five_passive_chain_fixture()
    assert _STRESS_OCCUPANCY_MIN <= layout.occupancy_ratio <= _STRESS_OCCUPANCY_MAX
    assert layout.frame == _STRESS_NOMINAL


def test_layout_stress_matches_global_occupancy_targets_on_default_frame() -> None:
    """Two-resistor baseline still hits 60–75% on DEFAULT_NOMINAL_FRAME."""
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    result = LayoutEngine(LayoutConfig(nominal_frame=DEFAULT_NOMINAL_FRAME)).layout(
        graph, {"r1": r1, "r2": r2}
    )
    assert OCCUPANCY_TARGET_MIN <= result.occupancy_ratio <= OCCUPANCY_TARGET_MAX


def test_layout_stress_wire_segments_no_illegal_overlap() -> None:
    _graph, _elements, layout = _five_passive_chain_fixture()
    boxes = [segment_bbox(seg) for wire in layout.wires for seg in wire.segments]
    for i, box_a in enumerate(boxes):
        for box_b in boxes[i + 1 :]:
            if not aabb_overlap(box_a, box_b):
                continue
            # Touching at endpoints is allowed; overlapping interior area is not.
            shared_corner = (
                box_a.min_x == box_b.max_x
                or box_b.min_x == box_a.max_x
                or box_a.min_y == box_b.max_y
                or box_b.min_y == box_a.max_y
            )
            assert shared_corner, (
                f"wire segment AABBs overlap without shared endpoint ({box_a}, {box_b})"
            )


def test_layout_stress_wire_replay_hash_deterministic() -> None:
    _graph, elements, layout_a = _five_passive_chain_fixture()
    layout_b = LayoutEngine(LayoutConfig(nominal_frame=_STRESS_NOMINAL)).layout(_graph, elements)
    digest_a = _wire_replay_digest(layout_a)
    digest_b = _wire_replay_digest(layout_b)
    assert digest_a == digest_b
    assert len(digest_a) == 64
