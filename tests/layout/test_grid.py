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


def test_place_on_grid_deterministic() -> None:

    r1 = Resistor("r1")

    r2 = Resistor("r2")

    first = place_on_grid((r2, r1))

    second = place_on_grid((r1, r2))

    assert first == second

    assert [placement.element_id for placement in first] == ["r1", "r2"]

    assert first[0].origin.x == 0.0

    assert first[1].origin.x == first[0].bounds.width + 0.5





def test_two_resistor_fixture_occupancy_in_target_band() -> None:

    placements = place_on_grid((Resistor("r1"), Resistor("r2")))

    bbox = layout_bbox(placements)

    ratio = occupancy_ratio(bbox, DEFAULT_NOMINAL_FRAME)

    assert OCCUPANCY_TARGET_MIN <= ratio <= OCCUPANCY_TARGET_MAX


