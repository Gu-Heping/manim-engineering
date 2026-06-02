"""Layout engine: grid placement + orthogonal routing for a circuit graph."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from manim_engineering.components.element import CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.core.exceptions import InvalidPortError
from manim_engineering.core.graph import CircuitGraph
from manim_engineering.layout.exceptions import UnknownElementError
from manim_engineering.layout.grid import (
    layout_bbox,
    occupancy_ratio,
    place_on_grid_semantic,
    scene_bbox,
)
from manim_engineering.layout.orientation import oriented_footprint, pin_local_in_aabb
from manim_engineering.layout.placement import placement_order_for_graph
from manim_engineering.layout.types import (
    DEFAULT_NOMINAL_FRAME,
    ComponentOrientation,
    ComponentPlacement,
    LabelPlacementMode,
    LayoutResult,
    Point2D,
    TextPlacementOverride,
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
    """Map a port to world coordinates via anchors, bounds, and optional orientation."""
    anchors = element.anchor_points
    if pin_name not in anchors:
        raise InvalidPortError(f"no anchor for pin {placement.element_id}.{pin_name}")
    anchor_x, anchor_y = anchors[pin_name]
    nominal = element.get_bounds()
    local = pin_local_in_aabb(anchor_x, anchor_y, nominal, placement.orientation)
    return Point2D(
        placement.origin.x + local.x,
        placement.origin.y + local.y,
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

    @property
    def config(self) -> LayoutConfig:
        """Public access to the immutable layout configuration."""

        return self._config

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
        *,
        placement_overrides: Mapping[str, Point2D] | None = None,
        orientation_overrides: Mapping[str, ComponentOrientation] | None = None,
        text_overrides: Mapping[str, Sequence[TextPlacementOverride]] | None = None,
        label_mode_overrides: Mapping[str, LabelPlacementMode] | None = None,
        net_waypoints: Mapping[str, Point2D] | None = None,
        connection_waypoints: Mapping[str, Sequence[Point2D]] | None = None,
    ) -> LayoutResult:
        """
        Place all graph nodes and route explicit connections.

        ``elements`` maps node id → ``CircuitElement`` instance attached to the graph.

        ``placement_overrides`` lets callers pin specific elements at exact world
        origins (bottom-left of each element's bounds). Unmapped elements still
        flow through ``place_on_grid``; pass an override map covering every
        element to bypass automatic placement entirely (canonical vertical-stack
        diagrams, manually-tuned analog topologies, etc.).

        ``net_waypoints`` maps deterministic net ids (see ``layout.nets``) to hub
        coordinates for star routing on 3+ pin nets.

        ``orientation_overrides`` maps element ids to discrete rotation / mirror
        transforms applied at placement time (see ``layout.orientation``).

        ``text_overrides`` maps element ids to manual upright label world positions
        per renderer text role (highest priority at render time).

        ``label_mode_overrides`` maps element ids to ``LabelPlacementMode`` (``AUTO``
        enables vertical band scoring; ``SLOT_ONLY`` uses type-based slots only).

        ``connection_waypoints`` maps connection ids to intermediate routing
        points for multi-leg orthogonal paths (e.g. GND detours below a bus).
        """
        self._elements_for_graph(graph, elements)
        overrides: Mapping[str, Point2D] = placement_overrides or {}
        orientations: Mapping[str, ComponentOrientation] = orientation_overrides or {}
        text_overrides_map: Mapping[str, Sequence[TextPlacementOverride]] = text_overrides or {}
        label_modes: Mapping[str, LabelPlacementMode] = label_mode_overrides or {}
        if overrides:
            unknown = sorted(set(overrides) - set(elements))
            if unknown:
                raise UnknownElementError(
                    f"placement_overrides reference unknown element id(s): {unknown}"
                )
        if orientations:
            unknown_orient = sorted(set(orientations) - set(elements))
            if unknown_orient:
                raise UnknownElementError(
                    f"orientation_overrides reference unknown element id(s): {unknown_orient}"
                )
        if text_overrides_map:
            unknown_text = sorted(set(text_overrides_map) - set(elements))
            if unknown_text:
                raise UnknownElementError(
                    f"text_overrides reference unknown element id(s): {unknown_text}"
                )
        if label_modes:
            unknown_modes = sorted(set(label_modes) - set(elements))
            if unknown_modes:
                raise UnknownElementError(
                    f"label_mode_overrides reference unknown element id(s): {unknown_modes}"
                )

        ordered_elements = placement_order_for_graph(graph, elements)
        grid_elements = tuple(
            element for element in ordered_elements if element.element_id not in overrides
        )
        grid_placements = place_on_grid_semantic(
            grid_elements,
            cell_gap=self._config.cell_gap,
        )

        manual_placements = tuple(
            ComponentPlacement(
                element_id=element.element_id,
                origin=overrides[element.element_id],
                bounds=element.get_bounds(),
            )
            for element in ordered_elements
            if element.element_id in overrides
        )

        placement_by_id = {
            placement.element_id: placement for placement in (*grid_placements, *manual_placements)
        }
        for element in ordered_elements:
            orientation = orientations.get(element.element_id)
            if orientation is None:
                continue
            placement = placement_by_id[element.element_id]
            oriented_bounds, _ = oriented_footprint(element.get_bounds(), orientation)
            placement_by_id[element.element_id] = ComponentPlacement(
                element_id=placement.element_id,
                origin=placement.origin,
                bounds=oriented_bounds,
                orientation=orientation,
                text_overrides=placement.text_overrides,
                label_mode=placement.label_mode,
            )
        for element in ordered_elements:
            text_override = text_overrides_map.get(element.element_id)
            label_mode = label_modes.get(element.element_id)
            if text_override is None and label_mode is None:
                continue
            placement = placement_by_id[element.element_id]
            placement_by_id[element.element_id] = ComponentPlacement(
                element_id=placement.element_id,
                origin=placement.origin,
                bounds=placement.bounds,
                orientation=placement.orientation,
                text_overrides=tuple(text_override)
                if text_override is not None
                else placement.text_overrides,
                label_mode=label_mode if label_mode is not None else placement.label_mode,
            )
        placements = tuple(placement_by_id[element.element_id] for element in ordered_elements)

        pin_positions: dict[str, Point2D] = {}
        for element in ordered_elements:
            placement = placement_by_id[element.element_id]
            for pin_name in sorted(element.pins):
                pin = element.get_pin(pin_name)
                pin_positions[pin.id] = pin_world_position(placement, element, pin_name)

        wires: list[WirePath] = []
        from manim_engineering.layout.nets import collect_junction_nodes, route_nets

        net_wp = net_waypoints or {}
        wires.extend(
            route_nets(
                graph.connections,
                pin_positions,
                elements,
                net_waypoints=net_wp,
                connection_waypoints=connection_waypoints,
                placements=placements,
            )
        )
        junction_nodes = collect_junction_nodes(
            graph.connections,
            pin_positions,
            net_waypoints=net_wp,
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
            junction_nodes=junction_nodes,
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
