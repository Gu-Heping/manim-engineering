"""Layout engine: grid placement + orthogonal routing for a circuit graph."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from manim_engineering.components.element import CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.core.exceptions import InvalidPortError
from manim_engineering.core.graph import CircuitGraph
from manim_engineering.layout.exceptions import UnknownElementError
from manim_engineering.layout.grid import layout_bbox, occupancy_ratio, place_on_grid, scene_bbox
from manim_engineering.layout.routing import (
    merge_routing_hints,
    points_to_segments,
    route_orthogonal,
)
from manim_engineering.layout.types import (
    DEFAULT_NOMINAL_FRAME,
    ComponentPlacement,
    LayoutResult,
    Point2D,
    WirePath,
)


@dataclass(frozen=True)
class LayoutConfig:
    """Configurable nominal frame and grid spacing for placement."""

    nominal_frame: Bounds = DEFAULT_NOMINAL_FRAME
    cell_gap: float = 0.5


def pin_world_position(
    placement: ComponentPlacement,
    element: CircuitElement,
    pin_name: str,
) -> Point2D:
    """Map a port to world coordinates via anchor points and bounds (not renderer geometry)."""
    anchors = element.anchor_points
    if pin_name not in anchors:
        raise InvalidPortError(f"no anchor for pin {placement.element_id}.{pin_name}")
    anchor_x, anchor_y = anchors[pin_name]
    bounds = element.get_bounds()
    return Point2D(
        placement.origin.x + anchor_x * bounds.width,
        placement.origin.y + anchor_y * bounds.height,
    )


def port_world_position(
    placement: ComponentPlacement,
    element: CircuitElement,
    port_name: str,
) -> Point2D:
    """Alias for :func:`pin_world_position`."""
    return pin_world_position(placement, element, port_name)


class LayoutEngine:
    """Orchestrates deterministic placement and connection routing for a graph."""

    def __init__(self, config: LayoutConfig | None = None) -> None:
        self._config = config or LayoutConfig()

    def solve(
        self,
        graph: CircuitGraph,
        elements: Mapping[str, CircuitElement],
    ) -> LayoutResult:
        """Place all graph nodes and route explicit connections."""
        return self.layout(graph, elements)

    def layout(
        self,
        graph: CircuitGraph,
        elements: Mapping[str, CircuitElement],
    ) -> LayoutResult:
        """
        Place all graph nodes and route explicit connections.

        ``elements`` maps node id → ``CircuitElement`` instance attached to the graph.
        """
        ordered_elements = self._elements_for_graph(graph, elements)
        placements = place_on_grid(
            ordered_elements,
            cell_gap=self._config.cell_gap,
        )
        placement_by_id = {placement.element_id: placement for placement in placements}

        pin_positions: dict[str, Point2D] = {}
        for element in ordered_elements:
            placement = placement_by_id[element.element_id]
            for pin_name in sorted(element.pins):
                pin = element.get_pin(pin_name)
                pin_positions[pin.id] = pin_world_position(placement, element, pin_name)

        wires: list[WirePath] = []
        for connection in graph.connections:
            start = pin_positions[connection.port_a.id]
            end = pin_positions[connection.port_b.id]
            hints = merge_routing_hints(
                connection.port_a.routing_hints,
                connection.port_b.routing_hints,
            )
            points = route_orthogonal(start, end, hints=hints)
            wires.append(
                WirePath(
                    connection_id=connection.id,
                    points=points,
                    segments=points_to_segments(points),
                )
            )

        bbox = layout_bbox(placements)
        scene = scene_bbox(placements, tuple(wires))
        ratio = occupancy_ratio(bbox, self._config.nominal_frame)

        return LayoutResult(
            placements=placements,
            pin_positions=pin_positions,
            wires=tuple(wires),
            frame=self._config.nominal_frame,
            occupancy_ratio=ratio,
            layout_bbox=bbox,
            scene_bbox=scene,
        )

    def _elements_for_graph(
        self,
        graph: CircuitGraph,
        elements: Mapping[str, CircuitElement],
    ) -> tuple[CircuitElement, ...]:
        ordered: list[CircuitElement] = []
        for node in graph.nodes:
            try:
                element = elements[node.id]
            except KeyError as exc:
                raise UnknownElementError(f"no circuit element for graph node: {node.id}") from exc
            if element.element_id != node.id:
                raise UnknownElementError(
                    f"element id mismatch: node {node.id} vs element {element.element_id}"
                )
            ordered.append(element)
        return tuple(ordered)
