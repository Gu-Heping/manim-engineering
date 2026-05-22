"""MinimalRenderer: deterministic Manim projection for layout-backed circuits."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
from manim import DL, Line, Text, VGroup, VMobject

from manim_engineering.components.common import VCC, Ground
from manim_engineering.components.element import CircuitElement
from manim_engineering.components.passive import Capacitor, Resistor
from manim_engineering.layout.types import ComponentPlacement, LayoutResult, Point2D
from manim_engineering.renderers.minimal import theme
from manim_engineering.semantic.graph import CircuitGraph


def _point3(p: Point2D) -> list[float]:
    return [p.x, p.y, 0.0]


def _line_between(start: Point2D, end: Point2D, *, color: object, width: float) -> Line:
    return Line(
        _point3(start),
        _point3(end),
        stroke_color=color,
        stroke_width=width,
    )


class MinimalRenderer:
    """Projects components and layout results into static Manim geometry."""

    def render(self, component: CircuitElement) -> VGroup:
        """Render a single component in local coordinates (origin = bounds bottom-left)."""
        if isinstance(component, Resistor):
            body = self._resistor_symbol(component)
        elif isinstance(component, Capacitor):
            body = self._capacitor_symbol(component)
        elif isinstance(component, Ground):
            body = self._ground_symbol(component)
        elif isinstance(component, VCC):
            body = self._vcc_symbol(component)
        else:
            body = self._generic_box(component)

        group = VGroup(body)
        if component.label:
            bounds = component.get_bounds()
            label = Text(
                component.label,
                font_size=0.18,
                color=theme.component_stroke_color(),
            )
            label.move_to(np.array([bounds.width * 0.5, bounds.height + 0.1, 0.0]))
            group.add(label)
        return group

    def render_layout(
        self,
        layout_result: LayoutResult,
        graph: CircuitGraph,
        elements: Mapping[str, CircuitElement],
    ) -> VGroup:
        """Compose placed component bodies and routed wires from a layout result."""
        connections = {connection.id: connection for connection in graph.connections}
        scene = VGroup()

        for placement in layout_result.placements:
            element = elements[placement.element_id]
            local = self.render(element)
            scene.add(self._place_at(local, placement))

        for wire in layout_result.wires:
            connection = connections[wire.connection_id]
            wire_color = theme.color_for_connection(connection)
            for segment in wire.segments:
                scene.add(
                    _line_between(
                        segment.start,
                        segment.end,
                        color=wire_color,
                        width=theme.WIRE_STROKE_WIDTH,
                    )
                )
        return scene

    def _place_at(self, mob: VMobject, placement: ComponentPlacement) -> VMobject:
        """Shift local geometry so bounds bottom-left sits at placement origin."""
        bl = mob.get_corner(DL)
        target = np.array([placement.origin.x, placement.origin.y, 0.0])
        mob.shift(target - bl)
        return mob

    def _resistor_symbol(self, component: Resistor) -> VGroup:
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        y = h * 0.5
        zig = 0.12 * h
        xs = (0.0, 0.2 * w, 0.4 * w, 0.6 * w, 0.8 * w, w)
        ys = (y, y + zig, y - zig, y + zig, y - zig, y)
        segments = VGroup(
            *[
                Line(
                    [xs[i], ys[i], 0.0],
                    [xs[i + 1], ys[i + 1], 0.0],
                    stroke_color=theme.component_stroke_color(),
                    stroke_width=theme.component_stroke_width(),
                )
                for i in range(len(xs) - 1)
            ]
        )
        return segments

    def _capacitor_symbol(self, component: Capacitor) -> VGroup:
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        y0, y1 = h * 0.2, h * 0.8
        gap = 0.08 * w
        cx = w * 0.5
        plate_kw = {
            "stroke_color": theme.component_stroke_color(),
            "stroke_width": theme.component_stroke_width(),
        }
        return VGroup(
            Line([cx - gap, y0, 0.0], [cx - gap, y1, 0.0], **plate_kw),
            Line([cx + gap, y0, 0.0], [cx + gap, y1, 0.0], **plate_kw),
            Line([0.0, h * 0.5, 0.0], [cx - gap, h * 0.5, 0.0], **plate_kw),
            Line([cx + gap, h * 0.5, 0.0], [w, h * 0.5, 0.0], **plate_kw),
        )

    def _ground_symbol(self, component: Ground) -> VGroup:
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        cx = w * 0.5
        stroke = {
            "stroke_color": theme.color_for_signal_type(component.get_pin("gnd").signal_type),
            "stroke_width": theme.component_stroke_width(),
        }
        lines = [
            Line([cx, h, 0.0], [cx, h * 0.55, 0.0], **stroke),
            Line([cx - 0.35 * w, h * 0.55, 0.0], [cx + 0.35 * w, h * 0.55, 0.0], **stroke),
            Line([cx - 0.25 * w, h * 0.38, 0.0], [cx + 0.25 * w, h * 0.38, 0.0], **stroke),
            Line([cx - 0.15 * w, h * 0.22, 0.0], [cx + 0.15 * w, h * 0.22, 0.0], **stroke),
        ]
        return VGroup(*lines)

    def _vcc_symbol(self, component: VCC) -> VGroup:
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        cx = w * 0.5
        stroke = {
            "stroke_color": theme.color_for_signal_type(component.get_pin("vcc").signal_type),
            "stroke_width": theme.component_stroke_width(),
        }
        return VGroup(
            Line([cx, 0.0, 0.0], [cx, h * 0.55, 0.0], **stroke),
            Line([cx - 0.35 * w, h * 0.55, 0.0], [cx + 0.35 * w, h * 0.55, 0.0], **stroke),
        )

    def _generic_box(self, component: CircuitElement) -> VGroup:
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        stroke = {
            "stroke_color": theme.component_stroke_color(),
            "stroke_width": theme.component_stroke_width(),
        }
        corners = [(0.0, 0.0), (w, 0.0), (w, h), (0.0, h), (0.0, 0.0)]
        edges = VGroup(
            *[
                Line(
                    [corners[i][0], corners[i][1], 0.0],
                    [corners[i + 1][0], corners[i + 1][1], 0.0],
                    **stroke,
                )
                for i in range(4)
            ]
        )
        return edges
