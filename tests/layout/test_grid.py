"""Grid placement and occupancy metric tests."""

from __future__ import annotations

from manim_engineering.components import Resistor
from manim_engineering.layout import (
    OCCUPANCY_TARGET_MAX,
    OCCUPANCY_TARGET_MIN,
    layout_bbox,
    occupancy_ratio,
    place_on_grid,
)
from manim_engineering.layout.types import DEFAULT_NOMINAL_FRAME


def test_place_on_grid_preserves_caller_order() -> None:

    r1 = Resistor("r1")

    r2 = Resistor("r2")

    left_to_right = place_on_grid((r1, r2))

    assert place_on_grid((r1, r2)) == left_to_right

    assert [placement.element_id for placement in left_to_right] == ["r1", "r2"]

    assert left_to_right[0].origin.x == 0.0

    assert left_to_right[1].origin.x == left_to_right[0].bounds.width + 0.5

    right_to_left = place_on_grid((r2, r1))

    assert [placement.element_id for placement in right_to_left] == ["r2", "r1"]


def test_two_resistor_fixture_occupancy_in_target_band() -> None:

    placements = place_on_grid((Resistor("r1"), Resistor("r2")))

    bbox = layout_bbox(placements)

    ratio = occupancy_ratio(bbox, DEFAULT_NOMINAL_FRAME)

    assert OCCUPANCY_TARGET_MIN <= ratio <= OCCUPANCY_TARGET_MAX
