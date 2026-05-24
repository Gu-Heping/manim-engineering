"""MinimalRenderer: deterministic Manim projection for layout-backed circuits."""

from __future__ import annotations

import os
from collections.abc import Mapping

import numpy as np
from manim import Circle, Dot, Line, Polygon, Rectangle, Text, VGroup, VMobject

from manim_engineering.components.analog import NMOS, NPN, PMOS, PNP, Diode, OpAmp, ZenerDiode
from manim_engineering.components.common import VCC, Ground, InputDriver
from manim_engineering.components.element import CircuitElement
from manim_engineering.components.passive import Capacitor, Inductor, Resistor
from manim_engineering.core.enums import SignalType
from manim_engineering.core.graph import CircuitGraph
from manim_engineering.layout.types import ComponentPlacement, LayoutResult, Point2D
from manim_engineering.renderers.minimal import theme
from manim_engineering.renderers.minimal.labels import WIRE_Z_INDEX, label_text


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
        elif isinstance(component, NMOS):
            body = self._nmos_symbol(component)
        elif isinstance(component, PMOS):
            body = self._pmos_symbol(component)
        elif isinstance(component, Diode):
            body = self._diode_symbol(component)
        elif isinstance(component, OpAmp):
            body = self._op_amp_symbol(component)
        elif isinstance(component, InputDriver):
            body = self._input_driver_symbol(component)
        elif isinstance(component, Inductor):
            body = self._inductor_symbol(component)
        elif isinstance(component, ZenerDiode):
            body = self._zener_symbol(component)
        elif isinstance(component, NPN):
            body = self._bjt_npn_symbol(component)
        elif isinstance(component, PNP):
            body = self._bjt_pnp_symbol(component)
        elif getattr(component, "semantic_type", "") == "interface":
            body = self._interface_box(component)
        else:
            body = self._generic_box(component)

        is_interface = getattr(component, "semantic_type", "") == "interface"
        skip_pin_dots = isinstance(component, (VCC, Ground, InputDriver)) or is_interface

        group = VGroup(body)
        if component.pins and not skip_pin_dots:
            group.add(self._pin_dots(component))
        if component.label:
            bounds = component.get_bounds()
            label = label_text(
                component.label,
                font_size=theme.COMPONENT_LABEL_FONT_SIZE,
                color=theme.component_stroke_color(),
            )
            label_y = (
                bounds.height
                + theme.COMPONENT_LABEL_Y_OFFSET * bounds.height
                + theme.COMPONENT_LABEL_FONT_SIZE * 0.02
            )
            if is_interface:
                label_y = _interface_component_label_y(body, bounds.height, label)
            elif isinstance(component, InputDriver):
                label_y = bounds.height + 0.18
            label.move_to(np.array([bounds.width * 0.5, label_y, 0.0]))
            group.add(label)
        if os.environ.get("DEBUG_RENDERER", "") == "1":
            group.add(self._debug_bounds_overlay(component))
        return group

    def render_circuit(
        self,
        graph: CircuitGraph,
        layout_result: LayoutResult,
        elements: Mapping[str, CircuitElement],
    ) -> VGroup:
        """Compose placed component bodies and routed wires from graph + layout."""
        return self.render_layout(layout_result, graph, elements)

    def render_layout(
        self,
        layout_result: LayoutResult,
        graph: CircuitGraph,
        elements: Mapping[str, CircuitElement],
    ) -> VGroup:
        """
        Compose placed component bodies and routed wires from a layout result.

        Submobject order (back → front): **components**, then **wires**.
        Scenes with a waveform panel should add ``components``, ``wires``, then the
        panel so nets stay under the timing strip.
        """
        connections = {connection.id: connection for connection in graph.connections}
        placed: list[VMobject] = []

        for placement in layout_result.placements:
            element = elements[placement.element_id]
            placed.append(self._place_at(self.render(element), placement))

        wire_lines: list[Line] = []
        junction_points: dict[tuple[float, float], int] = {}
        for wire in layout_result.wires:
            connection = connections[wire.connection_id]
            wire_color = theme.color_for_connection(connection)
            for segment in wire.segments:
                segment_line = _line_between(
                    segment.start,
                    segment.end,
                    color=wire_color,
                    width=theme.WIRE_STROKE_WIDTH,
                )
                segment_line.set_z_index(WIRE_Z_INDEX)
                wire_lines.append(segment_line)
                for pt in (segment.start, segment.end):
                    key = (round(pt.x, 6), round(pt.y, 6))
                    junction_points[key] = junction_points.get(key, 0) + 1
        junction_dots = self._render_node_junctions(junction_points)
        return VGroup(*placed, *wire_lines, *junction_dots)

    def _place_at(self, mob: VMobject, placement: ComponentPlacement) -> VMobject:
        """Shift local geometry so bounds bottom-left sits at placement origin."""
        mob.shift(np.array([placement.origin.x, placement.origin.y, 0.0]))
        return mob

    def _debug_bounds_overlay(self, component: CircuitElement) -> VGroup:
        """Dashed bounds rect + anchor dots when ``DEBUG_RENDERER=1``."""
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        from manim import DashedLine

        dash_kw = {"stroke_color": "#FF00FF", "stroke_width": 1.0, "dash_length": 0.08}
        rect_lines = [
            DashedLine([0, 0, 0], [w, 0, 0], **dash_kw),
            DashedLine([w, 0, 0], [w, h, 0], **dash_kw),
            DashedLine([w, h, 0], [0, h, 0], **dash_kw),
            DashedLine([0, h, 0], [0, 0, 0], **dash_kw),
        ]
        dots: list[Dot] = []
        for name, (ax, ay) in sorted(component.anchor_points.items()):
            if name == "center":
                continue
            dx = ax * w
            dy = ay * h
            d = Dot(point=[dx, dy, 0], radius=0.03, color="#00FFFF")
            label = Text(name, font_size=10, color="#00FFFF")
            label.move_to([dx + 0.08, dy + 0.08, 0])
            dots.extend([d, label])
        return VGroup(*rect_lines, *dots)

    def _pin_dots(self, component: CircuitElement) -> VGroup:
        """Terminal markers at declared anchor points (excludes ``center``)."""
        bounds = component.get_bounds()
        stroke = theme.component_stroke_color()
        radius = theme.pin_dot_radius()
        dots: list[Dot] = []
        for name, (ax, ay) in sorted(component.anchor_points.items()):
            if name == "center":
                continue
            dots.append(
                Dot(
                    point=[ax * bounds.width, ay * bounds.height, 0.0],
                    radius=radius,
                    color=stroke,
                )
            )
        return VGroup(*dots)

    def _render_node_junctions(self, point_counts: dict[tuple[float, float], int]) -> list[Dot]:
        """Small filled dots at wire vertices where 3+ segments meet (T-junctions).

        Points with count == 2 are normal straight/elbow wire joins and get no dot.
        """
        radius = theme.JUNCTION_DOT_RADIUS
        dots: list[Dot] = []
        for (px, py), count in point_counts.items():
            if count < 3:
                continue
            dots.append(Dot(
                point=[px, py, 0.0],
                radius=radius,
                color=theme.component_stroke_color(),
                fill_opacity=1.0,
            ))
        return dots

    def _resistor_symbol(self, component: Resistor) -> VGroup:
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        y = h * 0.5
        lead_in = 0.12 * w
        lead_out = 0.88 * w
        zig = theme.RESISTOR_ZIGZAG_AMPLITUDE * h
        stroke_kw = {
            "stroke_color": theme.component_stroke_color(),
            "stroke_width": theme.component_stroke_width(),
        }
        xs = (lead_in, 0.28 * w, 0.44 * w, 0.56 * w, 0.72 * w, lead_out)
        ys = (y, y + zig, y - zig, y + zig, y - zig, y)
        segments: list[Line] = [
            Line([0.0, y, 0.0], [lead_in, y, 0.0], **stroke_kw),
            Line([lead_out, y, 0.0], [w, y, 0.0], **stroke_kw),
        ]
        segments.extend(
            Line(
                [xs[i], ys[i], 0.0],
                [xs[i + 1], ys[i + 1], 0.0],
                **stroke_kw,
            )
            for i in range(len(xs) - 1)
        )
        return VGroup(*segments)

    def _capacitor_symbol(self, component: Capacitor) -> VGroup:
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        y0, y1 = h * 0.15, h * 0.85
        gap = theme.CAPACITOR_PLATE_GAP * w
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
        """GND with pin at top-centre (anchor ``gnd`` = ``(0.5, 1.0)``).

        Stub descends from the pin into three decreasing horizontal bars.
        Bar widths use theme constants for visibility across frame scales.
        """
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        cx = w * 0.5
        stroke = {
            "stroke_color": theme.color_for_signal_type(component.get_pin("gnd").signal_type),
            "stroke_width": theme.component_stroke_width(),
        }
        bar_top_y = h * 0.55
        bar_mid_y = h * 0.35
        bar_bot_y = h * 0.18
        return VGroup(
            Line([cx, h, 0.0], [cx, bar_top_y, 0.0], **stroke),
            Line(
                [cx - theme.GND_BAR_TOP * w, bar_top_y, 0.0],
                [cx + theme.GND_BAR_TOP * w, bar_top_y, 0.0],
                **stroke,
            ),
            Line(
                [cx - theme.GND_BAR_MID * w, bar_mid_y, 0.0],
                [cx + theme.GND_BAR_MID * w, bar_mid_y, 0.0],
                **stroke,
            ),
            Line(
                [cx - theme.GND_BAR_BOT * w, bar_bot_y, 0.0],
                [cx + theme.GND_BAR_BOT * w, bar_bot_y, 0.0],
                **stroke,
            ),
        )

    def _vcc_symbol(self, component: VCC) -> VGroup:
        """VCC with pin at bottom-centre (anchor ``vcc`` = ``(0.5, 0.0)``).

        Horizontal supply bar at the top; stub descends to the pin.
        Component label is handled by :meth:`render`.
        """
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        cx = w * 0.5
        power_color = theme.color_for_signal_type(component.get_pin("vcc").signal_type)
        stroke = {
            "stroke_color": power_color,
            "stroke_width": theme.component_stroke_width(),
        }
        bar_y = h * 0.55
        return VGroup(
            Line([cx - 0.35 * w, bar_y, 0.0], [cx + 0.35 * w, bar_y, 0.0], **stroke),
            Line([cx, bar_y, 0.0], [cx, 0.0, 0.0], **stroke),
        )

    def _nmos_symbol(self, component: NMOS) -> VGroup:
        """N-MOSFET for vertical CMOS stacks.

        Anchors (local coords, origin = bounds bottom-left):

        - ``gate``   ``(0, h/2)``
        - ``drain``  ``(w, h)``   — top horizontal lead
        - ``source`` ``(w, 0)``   — bottom horizontal lead + N-type arrow
        """
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        stroke = {
            "stroke_color": theme.color_for_signal_type(SignalType.ANALOG),
            "stroke_width": theme.component_stroke_width(),
        }

        channel_x = 0.55 * w
        gate_stub_x = 0.38 * w
        gate_y = 0.5 * h
        channel_bot = 0.10 * h
        channel_top = 0.90 * h

        segments: list[VMobject] = [
            Line([0.0, gate_y, 0.0], [gate_stub_x, gate_y, 0.0], **stroke),
            Line([gate_stub_x, channel_bot, 0.0], [gate_stub_x, channel_top, 0.0], **stroke),
            Line([channel_x, 0.0, 0.0], [channel_x, h, 0.0], **stroke),
            Line([channel_x, h, 0.0], [w, h, 0.0], **stroke),
            Line([channel_x, 0.0, 0.0], [w, 0.0, 0.0], **stroke),
        ]
        segments.append(_channel_arrow(channel_x + 0.04 * w, 0.0, w, inward=True))
        return VGroup(*segments)

    def _pmos_symbol(self, component: PMOS) -> VGroup:
        """P-MOSFET for vertical CMOS stacks.

        Same geometry as NMOS but **source** is the top lead ``(w, h)`` and
        **drain** is the bottom lead ``(w, 0)``, matching :class:`PMOS` anchors.
        Gate inversion bubble + P-type arrow on the source (top) lead.
        """
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        stroke = {
            "stroke_color": theme.color_for_signal_type(SignalType.ANALOG),
            "stroke_width": theme.component_stroke_width(),
        }

        channel_x = 0.55 * w
        gate_stub_x = 0.38 * w
        gate_y = 0.5 * h
        channel_bot = 0.10 * h
        channel_top = 0.90 * h
        bubble_radius = theme.PMOS_GATE_BUBBLE_RADIUS * w
        bubble_cx = gate_stub_x - bubble_radius

        bubble = Circle(radius=bubble_radius, **stroke)
        bubble.move_to([bubble_cx, gate_y, 0.0])
        segments = [
            Line([0.0, gate_y, 0.0], [bubble_cx - bubble_radius, gate_y, 0.0], **stroke),
            bubble,
            Line([gate_stub_x, channel_bot, 0.0], [gate_stub_x, channel_top, 0.0], **stroke),
            Line([channel_x, 0.0, 0.0], [channel_x, h, 0.0], **stroke),
            Line([channel_x, h, 0.0], [w, h, 0.0], **stroke),
            Line([channel_x, 0.0, 0.0], [w, 0.0, 0.0], **stroke),
        ]
        segments.append(_channel_arrow(channel_x + 0.04 * w, h, w, inward=False))
        return VGroup(*segments)

    def _diode_symbol(self, component: Diode) -> VGroup:
        """Filled triangle (anode→cathode) + cathode bar."""
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        analog_color = theme.color_for_signal_type(SignalType.ANALOG)
        stroke = {
            "stroke_color": analog_color,
            "stroke_width": theme.component_stroke_width(),
        }

        tri_base_x = 0.25 * w
        tri_tip_x = 0.65 * w
        bar_x = tri_tip_x
        y_mid = 0.5 * h
        y_top = 0.85 * h
        y_bot = 0.15 * h

        triangle = Polygon(
            [tri_base_x, y_top, 0.0],
            [tri_base_x, y_bot, 0.0],
            [tri_tip_x, y_mid, 0.0],
            fill_color=analog_color,
            fill_opacity=1.0,
            **stroke,
        )
        leads = [
            Line([0.0, y_mid, 0.0], [tri_base_x, y_mid, 0.0], **stroke),
            Line([tri_tip_x, y_mid, 0.0], [w, y_mid, 0.0], **stroke),
            Line([bar_x, y_top, 0.0], [bar_x, y_bot, 0.0], **stroke),
        ]
        return VGroup(triangle, *leads)

    def _op_amp_symbol(self, component: OpAmp) -> VGroup:
        """Right-pointing isoceles triangle + ``+`` / ``-`` glyphs + pin stubs."""
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        stroke = {
            "stroke_color": theme.color_for_signal_type(SignalType.ANALOG),
            "stroke_width": theme.component_stroke_width(),
        }

        # Triangle: left edge inset to leave room for input pin stubs.
        tri_left_x = 0.20 * w
        tri_right_x = 0.85 * w
        tri_top_y = 0.95 * h
        tri_bot_y = 0.05 * h
        tri_tip_y = 0.5 * h

        triangle = Polygon(
            [tri_left_x, tri_top_y, 0.0],
            [tri_left_x, tri_bot_y, 0.0],
            [tri_right_x, tri_tip_y, 0.0],
            **stroke,
        )
        leads = [
            # in_p stub (top-left)
            Line([0.0, 0.75 * h, 0.0], [tri_left_x, 0.75 * h, 0.0], **stroke),
            # in_n stub (bottom-left)
            Line([0.0, 0.25 * h, 0.0], [tri_left_x, 0.25 * h, 0.0], **stroke),
            # out stub
            Line([tri_right_x, tri_tip_y, 0.0], [w, tri_tip_y, 0.0], **stroke),
        ]

        plus_label = label_text(
            "+",
            font_size=theme.INTERFACE_PIN_FONT_SIZE,
            color=theme.color_for_signal_type(SignalType.ANALOG),
        )
        plus_label.move_to([tri_left_x + 0.12 * w, 0.75 * h, 0.0])

        minus_label = label_text(
            "-",
            font_size=theme.INTERFACE_PIN_FONT_SIZE,
            color=theme.color_for_signal_type(SignalType.ANALOG),
        )
        minus_label.move_to([tri_left_x + 0.12 * w, 0.25 * h, 0.0])

        return VGroup(triangle, *leads, plus_label, minus_label)

    def _input_driver_symbol(self, component: InputDriver) -> VGroup:
        """Right-pointing wedge whose tip sits at the ``out`` anchor."""
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        stroke_color = theme.color_for_signal_type(component.get_pin("out").signal_type)
        stroke_kw = {
            "stroke_color": stroke_color,
            "stroke_width": theme.component_stroke_width(),
        }

        tip_x = w
        base_x = w * 0.55
        y_mid = h * 0.5
        half_h = h * 0.35
        wedge = Polygon(
            [tip_x, y_mid, 0.0],
            [base_x, y_mid + half_h, 0.0],
            [base_x, y_mid - half_h, 0.0],
            fill_color=stroke_color,
            fill_opacity=1.0,
            **stroke_kw,
        )
        return VGroup(wedge)

    def _inductor_symbol(self, component: Inductor) -> VGroup:
        """Semicircle loops between horizontal leads."""
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        y = h * 0.5
        stroke_kw = {
            "stroke_color": theme.component_stroke_color(),
            "stroke_width": theme.component_stroke_width(),
        }
        lead_in = 0.10 * w
        lead_out = 0.90 * w
        n_loops = 3
        loop_w = (lead_out - lead_in) / n_loops
        loop_r = loop_w * 0.5
        segments = [
            Line([0.0, y, 0.0], [lead_in, y, 0.0], **stroke_kw),
            Line([lead_out, y, 0.0], [w, y, 0.0], **stroke_kw),
        ]
        for i in range(n_loops):
            cx = lead_in + (i + 0.5) * loop_w
            from manim import ArcBetweenPoints

            arc = ArcBetweenPoints(
                [cx - loop_r, y, 0.0],
                [cx + loop_r, y, 0.0],
                angle=-0.95 * np.pi,
                **stroke_kw,
            )
            segments.append(arc)
        return VGroup(*segments)

    def _zener_symbol(self, component: ZenerDiode) -> VGroup:
        """Filled triangle + cathode bar with bent arm (Zener distinct from rectifier)."""
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        analog = theme.color_for_signal_type(SignalType.ANALOG)
        stroke = {"stroke_color": analog, "stroke_width": theme.component_stroke_width()}

        tri_base_x = 0.25 * w
        tri_tip_x = 0.60 * w
        bar_x = tri_tip_x
        y_mid = 0.5 * h
        y_top = 0.85 * h
        y_bot = 0.15 * h

        triangle = Polygon(
            [tri_base_x, y_top, 0.0],
            [tri_base_x, y_bot, 0.0],
            [tri_tip_x, y_mid, 0.0],
            fill_color=analog, fill_opacity=1.0, **stroke,
        )
        bend_tip = 0.10 * w
        cathode_bar = Line([bar_x, y_top, 0.0], [bar_x, y_bot, 0.0], **stroke)
        cathode_bend = Line([bar_x, y_bot, 0.0], [bar_x + bend_tip, y_bot, 0.0], **stroke)
        leads = [
            Line([0.0, y_mid, 0.0], [tri_base_x, y_mid, 0.0], **stroke),
            Line([bar_x + bend_tip, y_bot, 0.0], [w, y_bot, 0.0], **stroke),
        ]
        return VGroup(triangle, cathode_bar, cathode_bend, *leads)

    def _bjt_npn_symbol(self, component: NPN) -> VGroup:
        """NPN: base left, collector top-right, emitter bottom-right (arrow outward)."""
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        analog = theme.color_for_signal_type(SignalType.ANALOG)
        stroke = {"stroke_color": analog, "stroke_width": theme.component_stroke_width()}

        base_x = 0.30 * w
        collector_x = 0.60 * w
        emitter_x = 0.60 * w
        base_y = 0.50 * h
        collector_y = 0.85 * h
        emitter_y = 0.15 * h

        vertical = Line([collector_x, emitter_y, 0.0], [collector_x, collector_y, 0.0], **stroke)
        base_stub = Line([0.0, base_y, 0.0], [base_x, base_y, 0.0], **stroke)
        collector_stub = Line([collector_x, collector_y, 0.0], [w, collector_y, 0.0], **stroke)
        emitter_stub = Line([emitter_x, emitter_y, 0.0], [w, emitter_y, 0.0], **stroke)
        emitter_arrow = Polygon(
            [emitter_x + 0.06 * w, emitter_y + 0.10 * h, 0.0],
            [emitter_x + 0.06 * w, emitter_y - 0.10 * h, 0.0],
            [emitter_x + 0.18 * w, emitter_y, 0.0],
            fill_color=analog, fill_opacity=1.0, **stroke,
        )
        return VGroup(vertical, base_stub, collector_stub, emitter_stub, emitter_arrow)

    def _bjt_pnp_symbol(self, component: PNP) -> VGroup:
        """PNP: base left, collector bottom-right, emitter top-right (arrow inward)."""
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        analog = theme.color_for_signal_type(SignalType.ANALOG)
        stroke = {"stroke_color": analog, "stroke_width": theme.component_stroke_width()}

        base_x = 0.30 * w
        collector_x = 0.60 * w
        emitter_x = 0.60 * w
        base_y = 0.50 * h
        collector_y = 0.15 * h
        emitter_y = 0.85 * h

        vertical = Line([collector_x, collector_y, 0.0], [collector_x, emitter_y, 0.0], **stroke)
        base_stub = Line([0.0, base_y, 0.0], [base_x, base_y, 0.0], **stroke)
        collector_stub = Line([collector_x, collector_y, 0.0], [w, collector_y, 0.0], **stroke)
        emitter_stub = Line([emitter_x, emitter_y, 0.0], [w, emitter_y, 0.0], **stroke)
        emitter_arrow = Polygon(
            [emitter_x + 0.06 * w, emitter_y + 0.10 * h, 0.0],
            [emitter_x + 0.06 * w, emitter_y - 0.10 * h, 0.0],
            [emitter_x - 0.06 * w, emitter_y, 0.0],
            fill_color=analog, fill_opacity=1.0, **stroke,
        )
        return VGroup(vertical, base_stub, collector_stub, emitter_stub, emitter_arrow)

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

    def _interface_panel_fill(self, width: float, height: float) -> Rectangle:
        """Opaque panel matching scene background so wires on top read as crossing a device."""
        panel = Rectangle(
            width=width,
            height=height,
            fill_color=theme.INTERFACE_PANEL_FILL,
            stroke_width=0,
        )
        panel.move_to(np.array([width * 0.5, height * 0.5, 0.0]))
        return panel

    def _interface_outline(self, component: CircuitElement) -> VGroup:
        """Hollow protocol device box (thin stroke, four lines — no fill)."""
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        stroke = {
            "stroke_color": theme.interface_box_stroke_color(),
            "stroke_width": theme.interface_box_stroke_width(),
        }
        corners = [(0.0, 0.0), (w, 0.0), (w, h), (0.0, h), (0.0, 0.0)]
        return VGroup(
            *[
                Line(
                    [corners[i][0], corners[i][1], 0.0],
                    [corners[i + 1][0], corners[i + 1][1], 0.0],
                    **stroke,
                )
                for i in range(4)
            ]
        )

    def _interface_box(self, component: CircuitElement) -> VGroup:
        """Protocol device: outline + role glyph + pin name labels on each anchor.

        Without this, SPI/UART devices render as identical featureless
        rectangles and viewers cannot tell which side drives which line.
        """
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        body = VGroup(self._interface_panel_fill(w, h), self._interface_outline(component))

        glyph = _role_glyph_for(component)
        if glyph:
            role = label_text(
                glyph,
                font_size=theme.INTERFACE_ROLE_FONT_SIZE,
                color=theme.component_stroke_color(),
            )
            role.move_to(np.array([w * 0.5, h * 0.5, 0.0]))
            body.add(role)

        anchors = component.anchor_points
        for pin_name, port in sorted(component.pins.items()):
            anchor = anchors.get(pin_name)
            if anchor is None:
                continue
            ax, ay = anchor
            pos = _interface_pin_label_position(pin_name, ax, ay, w, h, component)
            if pos is None:
                continue
            stroke = theme.color_for_signal_type(port.signal_type)
            pin_label = label_text(
                pin_name,
                font_size=theme.INTERFACE_PIN_FONT_SIZE,
                color=stroke,
            )
            pin_label.move_to(np.array([pos[0], pos[1], 0.0]))
            body.add(pin_label)
            # Direction stubs share the pin row and sit between the box and the label;
            # they read as a white/colored halo around the glyphs at teaching resolutions.
        return body


_ROLE_GLYPHS = {
    "SPIMaster": "M",
    "SPISlave": "S",
    "UARTPort": "U",
}


def _role_glyph_for(component: CircuitElement) -> str:
    name = type(component).__name__
    return _ROLE_GLYPHS.get(name, "")


_PIN_LABEL_OUTSIDE_MARGIN = 0.30
_INTERFACE_LABEL_CLEARANCE = 0.08


def _interface_component_label_y(body: VGroup, box_height: float, label: Text) -> float:
    """Place MCU/SLV name above the highest pin label with bbox clearance."""
    top = box_height
    for sub in body:
        if isinstance(sub, Text):
            top = max(top, float(sub.get_top()[1]))
    return top + _INTERFACE_LABEL_CLEARANCE + label.height / 2


def _interface_pin_label_position(
    pin_name: str,
    ax: float,
    ay: float,
    w: float,
    h: float,
    component: CircuitElement,
) -> tuple[float, float] | None:
    """Pin label center in local coords; ``None`` skips labels on the bus-facing edge."""
    comp_name = type(component).__name__
    if comp_name == "SPIMaster":
        if pin_name == "miso":
            return _pin_label_outside(ax, ay, w, h)
        if ax <= 0.05:
            return _pin_label_outside(ax, ay, w, h)
        return None
    if comp_name == "SPISlave":
        # MISO label only on master; slave side would overlap in the bus gap.
        if pin_name == "miso":
            return None
        if ax >= 0.95:
            return _pin_label_outside(ax, ay, w, h)
        return None
    if comp_name == "UARTPort":
        if ax <= 0.05 or ay <= 0.05:
            return _pin_label_outside(ax, ay, w, h)
        return None
    return _pin_label_outside(ax, ay, w, h)


def _pin_label_outside(ax: float, ay: float, w: float, h: float) -> tuple[float, float]:
    """Place pin label center outside the box edge (labels must not crowd the interior)."""
    margin = _PIN_LABEL_OUTSIDE_MARGIN
    px, py = ax * w, ay * h
    if ax <= 0.05:
        return px - margin, py
    if ax >= 0.95:
        return px + margin, py
    if ay <= 0.05:
        return px, py - margin
    if ay >= 0.95:
        return px, py + margin
    return px, py + margin


def _channel_arrow(channel_x: float, y: float, w: float, *, inward: bool) -> Polygon:
    """Small filled triangle marking N (``inward=True``) vs P (``inward=False``)
    MOSFET channel polarity. Drawn next to the channel bar at ``(channel_x, y)``.

    ``inward=True``  → tip points toward the channel (toward +x), base at left
    ``inward=False`` → tip points away from the channel (toward -x), base at right
    """
    size = theme.MOSFET_ARROW_SIZE * w
    if inward:
        tip = [channel_x, y, 0.0]
        base_top = [channel_x - size, y + size * 0.7, 0.0]
        base_bot = [channel_x - size, y - size * 0.7, 0.0]
    else:
        tip = [channel_x - size * 1.4, y, 0.0]
        base_top = [channel_x - size * 0.4, y + size * 0.7, 0.0]
        base_bot = [channel_x - size * 0.4, y - size * 0.7, 0.0]
    return Polygon(
        tip,
        base_top,
        base_bot,
        stroke_color=theme.color_for_signal_type(SignalType.ANALOG),
        stroke_width=theme.HELPER_STROKE_WIDTH,
        fill_color=theme.color_for_signal_type(SignalType.ANALOG),
        fill_opacity=1.0,
    )
