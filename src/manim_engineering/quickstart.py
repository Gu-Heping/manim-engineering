"""Task-level helpers for fast circuit assembly."""

from __future__ import annotations

import os
import shutil
import tempfile
from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from manim_engineering.components import VCC, Ground, InputDriver
from manim_engineering.components.element import CircuitElement
from manim_engineering.core import CircuitGraph, InvalidPortError
from manim_engineering.layout import (
    OCCUPANCY_TARGET_MAX,
    LayoutConfig,
    LayoutEngine,
    LayoutResult,
    Point2D,
)
from manim_engineering.layout.types import (
    ComponentOrientation,
    LabelPlacementMode,
    TextPlacementOverride,
)

ElementMap = Mapping[str, CircuitElement]
ConnectionSpec = tuple[str, str, str, str]
LayoutWarning = str


@dataclass(frozen=True)
class CircuitBuildResult:
    """Structured result from the quickstart graph assembly path."""

    graph: CircuitGraph
    elements: dict[str, CircuitElement]
    connections: tuple[ConnectionSpec, ...]


@dataclass(frozen=True)
class LayoutOutcome:
    """Quickstart layout result plus task-level diagnostics."""

    layout: LayoutResult
    layout_mode: str
    warnings: tuple[LayoutWarning, ...]
    needs_attention: bool


@dataclass(frozen=True)
class DiagramRenderResult:
    """Quickstart render result for static circuit diagrams."""

    rendered: Any
    topology: Any | None
    output_path: Path | None
    preview_attempted: bool
    preview_available: bool
    warnings: tuple[LayoutWarning, ...]


def build_circuit(
    elements: ElementMap | Sequence[tuple[str, CircuitElement]],
    connections: Sequence[ConnectionSpec],
) -> CircuitBuildResult:
    """
    Build a registered ``CircuitGraph`` from task-level element and connection specs.

    ``elements`` accepts either a mapping or an ordered ``[(id, element)]`` sequence.
    Each element id must match ``element.element_id``.

    ``connections`` uses ``(from_element_id, from_pin, to_element_id, to_pin)``
    tuples so callers do not need to manually ``attach_to`` components or plumb
    live ``Port`` objects through the graph layer.
    """

    normalized = _normalize_elements(elements)
    graph = CircuitGraph()

    for element in normalized.values():
        element.attach_to(graph)

    for from_id, from_pin, to_id, to_pin in connections:
        try:
            source = normalized[from_id]
        except KeyError as exc:
            raise KeyError(f"unknown connection source element: {from_id}") from exc
        try:
            target = normalized[to_id]
        except KeyError as exc:
            raise KeyError(f"unknown connection target element: {to_id}") from exc

        try:
            graph.connect(source.get_port(from_pin), target.get_port(to_pin))
        except InvalidPortError as exc:
            raise InvalidPortError(
                f"invalid connection {from_id}.{from_pin} -> {to_id}.{to_pin}: {exc}"
            ) from exc

    return CircuitBuildResult(
        graph=graph,
        elements=normalized,
        connections=tuple(connections),
    )


def layout_circuit(
    build: CircuitBuildResult,
    *,
    engine: LayoutEngine | None = None,
    config: LayoutConfig | None = None,
    placement_overrides: Mapping[str, Point2D] | None = None,
    orientation_overrides: Mapping[str, ComponentOrientation] | None = None,
    text_overrides: Mapping[str, Sequence[TextPlacementOverride]] | None = None,
    label_mode_overrides: Mapping[str, LabelPlacementMode] | None = None,
    net_waypoints: Mapping[str, Point2D] | None = None,
    connection_waypoints: Mapping[str, Sequence[Point2D]] | None = None,
) -> LayoutOutcome:
    """
    Run the canonical layout path and attach task-level warnings.

    This does not change ``LayoutEngine`` behavior. It wraps the current deterministic
    layout path with machine-readable diagnostics so agents and users can detect
    layouts that likely need presets or manual refinement.
    """

    layout_engine = engine or LayoutEngine(config)
    effective_overrides = placement_overrides
    layout_mode = "manual" if placement_overrides else "semantic_grid"
    if (
        effective_overrides is None
        and net_waypoints is None
        and connection_waypoints is None
        and _has_branching_topology(build.graph)
    ):
        effective_overrides = _structured_branching_overrides(
            build,
            cell_gap=layout_engine._config.cell_gap,
        )
        layout_mode = "structured_auto"

    layout = layout_engine.layout(
        build.graph,
        build.elements,
        placement_overrides=effective_overrides,
        orientation_overrides=orientation_overrides,
        text_overrides=text_overrides,
        label_mode_overrides=label_mode_overrides,
        net_waypoints=net_waypoints,
        connection_waypoints=connection_waypoints,
    )
    warnings = _layout_warnings(
        build,
        layout,
        placement_overrides=effective_overrides,
        net_waypoints=net_waypoints,
        connection_waypoints=connection_waypoints,
    )
    return LayoutOutcome(
        layout=layout,
        layout_mode=layout_mode,
        warnings=warnings,
        needs_attention=bool(warnings),
    )


def render_circuit_diagram(
    build: CircuitBuildResult,
    layout_outcome: LayoutOutcome,
    *,
    renderer: Any | None = None,
    include_topology: bool = True,
    output_path: str | Path | None = None,
    preview: bool = False,
) -> DiagramRenderResult:
    """
    Render a static circuit diagram from quickstart build + layout results.

    When ``output_path`` is provided, this helper exports a PNG preview of the
    rendered group using a minimal one-frame Manim scene. ``preview=True`` then
    attempts to open that PNG through the host OS when supported.
    """

    if renderer is None:
        from manim_engineering.renderers.minimal import ManimRenderer

        renderer = ManimRenderer()

    rendered = renderer.render(build.graph, layout_outcome.layout, build.elements)
    topology = None
    if include_topology:
        topology = renderer.render_topology(build.graph, layout_outcome.layout, build.elements)

    warnings = layout_outcome.warnings
    exported_path: Path | None = None
    preview_available = False
    if output_path is not None:
        exported_path = export_circuit_preview(rendered, output_path)
        if preview:
            preview_available = _open_preview(exported_path)
            if not preview_available:
                warnings = (*warnings, "preview.open_unavailable")
    elif preview:
        warnings = (*warnings, "preview.requires_output_path")

    return DiagramRenderResult(
        rendered=rendered,
        topology=topology,
        output_path=exported_path,
        preview_attempted=preview,
        preview_available=preview_available,
        warnings=warnings,
    )


def export_circuit_preview(
    rendered: Any,
    output_path: str | Path,
    *,
    background_color: str = "#1e1e2e",
) -> Path:
    """Export a static PNG preview for a rendered circuit group."""

    from manim import Scene, tempconfig

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    class _PreviewScene(Scene):
        def construct(self) -> None:
            self.add(rendered.copy())

    with tempfile.TemporaryDirectory(prefix="me_quickstart_preview_") as tmpdir:
        with tempconfig(
            {
                "quality": "low_quality",
                "disable_caching": True,
                "media_dir": tmpdir,
                "write_to_movie": False,
                "save_last_frame": True,
                "background_color": background_color,
            }
        ):
            _PreviewScene().render()
        matches = sorted(Path(tmpdir).rglob("_PreviewScene*.png"))
        if not matches:
            raise FileNotFoundError(f"no PNG export produced under {tmpdir}")
        shutil.copy2(matches[-1], destination)
    return destination


def _open_preview(path: Path) -> bool:
    """Best-effort preview opener for exported images."""

    if hasattr(os, "startfile"):
        os.startfile(str(path))
        return True
    return False


def _normalize_elements(
    elements: ElementMap | Sequence[tuple[str, CircuitElement]],
) -> dict[str, CircuitElement]:
    if isinstance(elements, Mapping):
        items = tuple(elements.items())
    else:
        items = tuple(elements)

    normalized: dict[str, CircuitElement] = {}
    for element_id, element in items:
        if element_id in normalized:
            raise ValueError(f"duplicate element id in build_circuit: {element_id}")
        if element.element_id != element_id:
            raise ValueError(
                "element id mismatch in build_circuit: "
                f"key {element_id!r} does not match element.element_id {element.element_id!r}"
            )
        normalized[element_id] = element
    return normalized


def _layout_warnings(
    build: CircuitBuildResult,
    layout: LayoutResult,
    *,
    placement_overrides: Mapping[str, Point2D] | None,
    net_waypoints: Mapping[str, Point2D] | None,
    connection_waypoints: Mapping[str, Sequence[Point2D]] | None,
) -> tuple[LayoutWarning, ...]:
    warnings: list[LayoutWarning] = []

    if layout.occupancy_ratio > OCCUPANCY_TARGET_MAX:
        warnings.append("layout.occupancy_above_target")

    auto_layout = not placement_overrides and not net_waypoints and not connection_waypoints
    unique_rows = {round(placement.origin.y, 6) for placement in layout.placements}
    if auto_layout and len(unique_rows) == 1 and len(layout.placements) >= 6:
        warnings.append("layout.single_row_auto_grid")

    if auto_layout and _has_branching_topology(build.graph):
        warnings.append("layout.branching_topology_using_auto_grid")

    return tuple(warnings)


def _has_branching_topology(graph: CircuitGraph) -> bool:
    degree_by_node: dict[str, set[str]] = {}
    for connection in graph.connections:
        a = connection.port_a.owner_id
        b = connection.port_b.owner_id
        degree_by_node.setdefault(a, set()).add(b)
        degree_by_node.setdefault(b, set()).add(a)
    return any(len(neighbors) > 2 for neighbors in degree_by_node.values())


def _structured_branching_overrides(
    build: CircuitBuildResult,
    *,
    cell_gap: float,
) -> dict[str, Point2D]:
    adjacency = _node_adjacency(build.graph)
    ordered_ids = _layered_node_ids(build, adjacency)
    elements = build.elements

    max_width = max(element.get_bounds().width for element in elements.values())
    max_height = max(element.get_bounds().height for element in elements.values())
    x_step = max_width + cell_gap
    y_step = max_height + cell_gap

    layer_members: dict[int, list[str]] = {}
    depths = _bfs_depths(ordered_ids[0], adjacency)
    for element_id in ordered_ids:
        layer_members.setdefault(depths[element_id], []).append(element_id)

    overrides: dict[str, Point2D] = {}
    for depth in sorted(layer_members):
        members = layer_members[depth]
        vertical_mid = (len(members) - 1) / 2.0
        for index, element_id in enumerate(members):
            element = elements[element_id]
            bounds = element.get_bounds()
            x = depth * x_step
            center_y = (vertical_mid - index) * y_step
            overrides[element_id] = Point2D(x, center_y - bounds.height * 0.5)
    return overrides


def _node_adjacency(graph: CircuitGraph) -> dict[str, tuple[str, ...]]:
    neighbors: dict[str, set[str]] = {node.id: set() for node in graph.nodes}
    for connection in graph.connections:
        a = connection.port_a.owner_id
        b = connection.port_b.owner_id
        neighbors.setdefault(a, set()).add(b)
        neighbors.setdefault(b, set()).add(a)
    return {node_id: tuple(sorted(adjacent)) for node_id, adjacent in neighbors.items()}


def _layered_node_ids(
    build: CircuitBuildResult,
    adjacency: Mapping[str, Sequence[str]],
) -> tuple[str, ...]:
    root = _preferred_root(build, adjacency)
    depths = _bfs_depths(root, adjacency)
    return tuple(sorted(adjacency, key=lambda node_id: (depths[node_id], node_id)))


def _preferred_root(
    build: CircuitBuildResult,
    adjacency: Mapping[str, Sequence[str]],
) -> str:
    input_nodes = sorted(
        element_id
        for element_id, element in build.elements.items()
        if isinstance(element, InputDriver)
    )
    if input_nodes:
        return input_nodes[0]

    power_nodes = sorted(
        element_id
        for element_id, element in build.elements.items()
        if isinstance(element, VCC)
    )
    if power_nodes:
        return power_nodes[0]

    leaves = sorted(node_id for node_id, neighbors in adjacency.items() if len(neighbors) <= 1)
    non_ground_leaves = [
        node_id for node_id in leaves if not isinstance(build.elements[node_id], Ground)
    ]
    if non_ground_leaves:
        return non_ground_leaves[0]
    if leaves:
        return leaves[0]
    return sorted(adjacency)[0]


def _bfs_depths(root: str, adjacency: Mapping[str, Sequence[str]]) -> dict[str, int]:
    depths = {root: 0}
    queue: deque[str] = deque([root])
    while queue:
        node_id = queue.popleft()
        base_depth = depths[node_id]
        for neighbor in adjacency[node_id]:
            if neighbor in depths:
                continue
            depths[neighbor] = base_depth + 1
            queue.append(neighbor)
    for node_id in adjacency:
        depths.setdefault(node_id, max(depths.values(), default=0) + 1)
    return depths
