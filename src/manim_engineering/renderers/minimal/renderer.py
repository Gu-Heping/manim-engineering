"""MinimalRenderer: deterministic Manim projection for layout-backed circuits."""

from __future__ import annotations

import math
import os
from collections.abc import Mapping

import numpy as np
from manim import DashedLine, Dot, Line, Polygon, Rectangle, RIGHT, Text, UP, VGroup, VMobject

from manim_engineering.components.analog import (
    NMOS,
    NMOSDepletion,
    NPN,
    PMOS,
    PMOSDepletion,
    PNP,
    Diode,
    OpAmp,
    ZenerDiode,
)
from manim_engineering.components.common import VCC, Ground, InputDriver
from manim_engineering.components.element import CircuitElement
from manim_engineering.components.types import Bounds
from manim_engineering.components.passive import Capacitor, Inductor, Resistor
from manim_engineering.core.enums import SignalType
from manim_engineering.core.graph import CircuitGraph
from manim_engineering.layout.nets import connection_for_wire
from manim_engineering.layout.orientation import oriented_footprint
from manim_engineering.layout.types import ComponentPlacement, LayoutResult, Point2D
from manim_engineering.components.analog.mosfet import ConductionMode
from manim_engineering.renderers.minimal import theme
from manim_engineering.renderers.minimal.conventions import MosfetSymbolConvention
from manim_engineering.renderers.minimal.labels import WIRE_Z_INDEX, label_text
from manim_engineering.renderers.minimal.text_placement import place_component_mob

_MOS_P_TYPES = (PMOS, PMOSDepletion)
_MOS_N_TYPES = (NMOS, NMOSDepletion)
_MOS_TYPES = _MOS_P_TYPES + _MOS_N_TYPES


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

    def __init__(
        self,
        *,
        mosfet_convention: MosfetSymbolConvention | None = None,
    ) -> None:
        self._mosfet_convention = mosfet_convention or MosfetSymbolConvention.textbook_vertical

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
        elif isinstance(component, _MOS_TYPES):
            body = self._mosfet_component_symbol(component)
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
            body = self._bjt_symbol(component, pnp=False)
        elif isinstance(component, PNP):
            body = self._bjt_symbol(component, pnp=True)
        elif getattr(component, "semantic_type", "") == "interface":
            body = self._interface_box(component)
        else:
            body = self._generic_box(component)

        is_interface = getattr(component, "semantic_type", "") == "interface"
        skip_pin_dots = isinstance(component, (VCC, Ground, InputDriver, NPN, PNP)) or is_interface

        group = VGroup(body)
        if component.pins and not skip_pin_dots:
            group.add(self._pin_dots(component))
        if component.label:
            bounds = component.get_bounds()
            label = label_text(
                component.label,
                font_size=theme.COMPONENT_LABEL_FONT_SIZE,
                color=theme.component_stroke_color(),
                role="component_label",
            )
            if isinstance(component, Ground):
                label.move_to(
                    np.array(
                        [
                            bounds.width * 0.5,
                            -theme.POWER_LABEL_BELOW_OFFSET,
                            0.0,
                        ]
                    )
                )
            elif isinstance(component, VCC):
                label.move_to(
                    np.array(
                        [
                            bounds.width * 0.5,
                            bounds.height + theme.POWER_LABEL_ABOVE_OFFSET,
                            0.0,
                        ]
                    )
                )
            elif isinstance(component, _MOS_TYPES):
                # Gate-height label to the left — stable in grids and CMOS stacks.
                # (Split above/below by polarity collides when rows are close.)
                label.move_to(
                    np.array(
                        [
                            -theme.MOSFET_LABEL_LEFT_OFFSET * bounds.width,
                            bounds.height * 0.5,
                            0.0,
                        ]
                    )
                )
            elif isinstance(
                component, (NPN, PNP, OpAmp, ZenerDiode, Diode)
            ):
                label_y = (
                    -theme.COMPONENT_LABEL_Y_OFFSET * bounds.height
                    - theme.COMPONENT_LABEL_FONT_SIZE * 0.02
                )
                label.move_to(np.array([bounds.width * 0.5, label_y, 0.0]))
            else:
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
            placed.append(
                self._place_component(
                    self.render(element),
                    placement,
                    element,
                    layout=layout_result,
                )
            )

        wire_lines: list[Line] = []
        junction_points: dict[tuple[float, float], int] = {}
        for wire in layout_result.wires:
            connection = connection_for_wire(wire, connections)
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
        junction_dots = self._render_node_junctions(
            junction_points,
            layout_result.junction_nodes,
        )
        return VGroup(*placed, *wire_lines, *junction_dots)

    def _place_component(
        self,
        mob: VMobject,
        placement: ComponentPlacement,
        element: CircuitElement,
        *,
        layout=None,
    ) -> VMobject:
        """Orient stroke geometry; reposition ``label_text`` upright in world space."""
        nominal = element.get_bounds()

        def _orient(geometry: VMobject, oriented_placement: ComponentPlacement) -> VMobject:
            return self._place_geometry_at(geometry, oriented_placement, nominal)

        return place_component_mob(
            mob,
            placement,
            nominal,
            element,
            place_geometry=_orient,
            layout=layout,
        )

    def _place_at(
        self,
        mob: VMobject,
        placement: ComponentPlacement,
        element: CircuitElement,
    ) -> VMobject:
        """Legacy path: orient full mob including labels (unit tests only)."""
        return self._place_geometry_at(mob, placement, element.get_bounds())

    def _place_geometry_at(
        self,
        mob: VMobject,
        placement: ComponentPlacement,
        nominal: Bounds,
    ) -> VMobject:
        """Shift and orient local geometry so the footprint AABB sits at placement origin."""
        w, h = nominal.width, nominal.height
        orientation = placement.orientation
        center = np.array([w / 2, h / 2, 0.0])

        # Manim: flip(UP) mirrors x (layout flip_x); flip(RIGHT) mirrors y (layout flip_y).
        if orientation.flip_x:
            mob.flip(UP, about_point=center)
        if orientation.flip_y:
            mob.flip(RIGHT, about_point=center)
        if orientation.rotation:
            mob.rotate(-math.radians(orientation.rotation), about_point=center)

        _aabb, offset = oriented_footprint(nominal, orientation)
        mob.shift(np.array([placement.origin.x - offset.x, placement.origin.y - offset.y, 0.0]))
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
        skip_pins: set[str] = set()
        if isinstance(component, _MOS_TYPES):
            skip_pins.add("bulk")
        dots: list[Dot] = []
        for name, (ax, ay) in sorted(component.anchor_points.items()):
            if name == "center" or name in skip_pins:
                continue
            dots.append(
                Dot(
                    point=[ax * bounds.width, ay * bounds.height, 0.0],
                    radius=radius,
                    color=stroke,
                )
            )
        return VGroup(*dots)

    def _render_node_junctions(
        self,
        point_counts: dict[tuple[float, float], int],
        electrical_nodes: frozenset[Point2D],
    ) -> list[Dot]:
        """Dots at T-junctions (3+ segments) and declared electrical junction nodes."""
        radius = theme.JUNCTION_DOT_RADIUS
        dots: list[Dot] = []
        seen: set[tuple[float, float]] = set()
        electrical_keys = {
            (round(node.x, 6), round(node.y, 6)) for node in electrical_nodes
        }

        def _add_dot(px: float, py: float) -> None:
            key = (px, py)
            if key in seen:
                return
            seen.add(key)
            dots.append(
                Dot(
                    point=[px, py, 0.0],
                    radius=radius,
                    color=theme.component_stroke_color(),
                    fill_opacity=1.0,
                )
            )

        for (px, py), count in point_counts.items():
            if count >= 3:
                _add_dot(px, py)

        for px, py in sorted(electrical_keys):
            _add_dot(px, py)

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

    def _mosfet_component_symbol(self, component: CircuitElement) -> VGroup:
        p_channel = getattr(component, "channel_polarity", "n") == "p"
        mode: ConductionMode = getattr(component, "conduction_mode", "enhancement")
        return _mosfet_symbol(
            component.get_bounds(),
            p_channel=p_channel,
            conduction_mode=mode,
            convention=self._mosfet_convention,
        )

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
            role="opamp.plus",
        )
        plus_label.move_to([tri_left_x + 0.12 * w, 0.75 * h, 0.0])

        minus_label = label_text(
            "-",
            font_size=theme.INTERFACE_PIN_FONT_SIZE,
            color=theme.color_for_signal_type(SignalType.ANALOG),
            role="opamp.minus",
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
        cathode_bend = Line([bar_x, y_mid, 0.0], [bar_x + bend_tip, y_mid, 0.0], **stroke)
        leads = [
            Line([0.0, y_mid, 0.0], [tri_base_x, y_mid, 0.0], **stroke),
            Line([bar_x + bend_tip, y_mid, 0.0], [w, y_mid, 0.0], **stroke),
        ]
        return VGroup(triangle, cathode_bar, cathode_bend, *leads)

    def _bjt_emitter_arrow(
        self,
        bar_x: float,
        bar_y: float,
        knee_x: float,
        knee_y: float,
        *,
        inward: bool,
        stroke: dict,
        fill_color,
    ) -> Polygon:
        """Filled arrow on the emitter diagonal (inward for PNP, outward for NPN)."""
        size = theme.BJT_EMITTER_ARROW_SIZE * max(knee_x - bar_x, 0.01)
        along_x = knee_x - bar_x
        along_y = knee_y - bar_y
        span = math.hypot(along_x, along_y) or 1.0
        leg_ux = along_x / span
        leg_uy = along_y / span
        ux, uy = leg_ux, leg_uy
        if inward:
            ux, uy = -ux, -uy
        leg_frac = (
            1.0 - theme.BJT_EMITTER_ARROW_LEG_FRAC
            if inward
            else theme.BJT_EMITTER_ARROW_LEG_FRAC
        )
        mid_x = bar_x + along_x * leg_frac
        mid_y = bar_y + along_y * leg_frac
        tip = [
            mid_x + ux * size * theme.BJT_EMITTER_ARROW_TIP_LEAD,
            mid_y + uy * size * theme.BJT_EMITTER_ARROW_TIP_LEAD,
            0.0,
        ]
        tail = [
            mid_x - ux * size * theme.BJT_EMITTER_ARROW_TAIL_TRAIL,
            mid_y - uy * size * theme.BJT_EMITTER_ARROW_TAIL_TRAIL,
            0.0,
        ]
        half_w = size * 0.40
        perp_x, perp_y = -uy, ux
        return Polygon(
            tip,
            [tail[0] + perp_x * half_w, tail[1] + perp_y * half_w, 0.0],
            [tail[0] - perp_x * half_w, tail[1] - perp_y * half_w, 0.0],
            fill_color=fill_color,
            fill_opacity=1.0,
            **stroke,
        )

    def _bjt_symbol(self, component: NPN | PNP, *, pnp: bool) -> VGroup:
        """Textbook open BJT: base bar, diagonal c/e legs, vertical stubs to pins."""
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        analog = theme.color_for_signal_type(SignalType.ANALOG)
        stroke = {"stroke_color": analog, "stroke_width": theme.component_stroke_width()}

        bar_x = theme.BJT_BASE_BAR_X * w
        stub_x = theme.BJT_STUB_X * w
        base_y = 0.5 * h
        bar_top = theme.BJT_BAR_TOP_Y * h
        bar_bot = theme.BJT_BAR_BOT_Y * h
        branch_top = theme.BJT_BAR_BRANCH_TOP_Y * h
        branch_bot = theme.BJT_BAR_BRANCH_BOT_Y * h
        knee_c = theme.BJT_STUB_KNEE_C_Y * h
        knee_e = theme.BJT_STUB_KNEE_E_Y * h

        if pnp:
            pin_c_y = 0.0
            pin_e_y = h
            emit_branch_y = branch_top
            emit_knee_y = knee_c
            coll_branch_y = branch_bot
            coll_knee_y = knee_e
            arrow_inward = True
        else:
            pin_c_y = h
            pin_e_y = 0.0
            emit_branch_y = branch_bot
            emit_knee_y = knee_e
            coll_branch_y = branch_top
            coll_knee_y = knee_c
            arrow_inward = False

        segments: list[VMobject] = [
            Line([0.0, base_y, 0.0], [bar_x, base_y, 0.0], **stroke),
            Line([bar_x, bar_bot, 0.0], [bar_x, bar_top, 0.0], **stroke),
            Line([bar_x, coll_branch_y, 0.0], [stub_x, coll_knee_y, 0.0], **stroke),
            Line([stub_x, coll_knee_y, 0.0], [stub_x, pin_c_y, 0.0], **stroke),
            Line([bar_x, emit_branch_y, 0.0], [stub_x, emit_knee_y, 0.0], **stroke),
            Line([stub_x, emit_knee_y, 0.0], [stub_x, pin_e_y, 0.0], **stroke),
            self._bjt_emitter_arrow(
                bar_x,
                emit_branch_y,
                stub_x,
                emit_knee_y,
                inward=arrow_inward,
                stroke=stroke,
                fill_color=analog,
            ),
        ]
        return VGroup(*segments)

    def _bjt_npn_symbol(self, component: NPN) -> VGroup:
        """NPN: base left, collector top-right, emitter bottom-right (arrow outward)."""
        return self._bjt_symbol(component, pnp=False)

    def _bjt_pnp_symbol(self, component: PNP) -> VGroup:
        """PNP: base left, collector bottom-right, emitter top-right (arrow inward)."""
        return self._bjt_symbol(component, pnp=True)

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
                role="interface.role",
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
                role=f"interface.pin.{pin_name}",
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


def _mosfet_symbol(
    bounds,
    *,
    p_channel: bool,
    conduction_mode: ConductionMode,
    convention: MosfetSymbolConvention,
) -> VGroup:
    """Route to textbook-vertical (default) or legacy horizontal-stub decoration."""
    if convention is MosfetSymbolConvention.textbook_vertical:
        return _mosfet_symbol_textbook_vertical(
            bounds,
            p_channel=p_channel,
            conduction_mode=conduction_mode,
        )
    return _mosfet_symbol_legacy_horizontal(
        bounds,
        p_channel=p_channel,
        conduction_mode=conduction_mode,
        convention=convention,
    )


def _channel_third_centers(channel_bot: float, channel_top: float) -> tuple[float, float, float]:
    span = channel_top - channel_bot
    gap = theme.MOSFET_SEGMENT_GAP * span
    bar = (span - 2.0 * gap) / 3.0
    return (
        channel_bot + bar * 0.5,
        channel_bot + bar + gap + bar * 0.5,
        channel_bot + 2.0 * bar + 2.0 * gap + bar * 0.5,
    )


def _enhancement_channel_thirds(
    channel_x: float,
    channel_bot: float,
    channel_top: float,
    *,
    stroke: dict,
) -> list[Line]:
    """Three equal discrete channel bars (enhancement); not a single dashed stroke."""
    span = channel_top - channel_bot
    gap = theme.MOSFET_SEGMENT_GAP * span
    bar = (span - 2.0 * gap) / 3.0
    segments: list[Line] = []
    for index in range(3):
        y0 = channel_bot + index * (bar + gap)
        y1 = y0 + bar
        segments.append(Line([channel_x, y0, 0.0], [channel_x, y1, 0.0], **stroke))
    return segments


def _bulk_horizontal_arrow(
    channel_x: float,
    export_x: float,
    branch_y: float,
    *,
    point_left: bool,
    stroke: dict,
) -> Polygon:
    """Filled triangle on the bulk stub (N: left toward channel, P: right away)."""
    size = theme.MOSFET_BODY_ARROW_SIZE
    mid_x = channel_x + (export_x - channel_x) * 0.38
    half_w = size * 0.42
    if point_left:
        tip = [mid_x - size * 0.45, branch_y, 0.0]
        base_c = [mid_x + size * 0.35, branch_y, 0.0]
    else:
        tip = [mid_x + size * 0.45, branch_y, 0.0]
        base_c = [mid_x - size * 0.35, branch_y, 0.0]
    return Polygon(
        tip,
        [base_c[0], base_c[1] + half_w, 0.0],
        [base_c[0], base_c[1] - half_w, 0.0],
        fill_color=stroke["stroke_color"],
        fill_opacity=1.0,
        **stroke,
    )


def _mosfet_symbol_textbook_vertical(
    bounds,
    *,
    p_channel: bool,
    conduction_mode: ConductionMode,
) -> VGroup:
    """Textbook vertical four-terminal glyph (three-part enhancement channel)."""
    w, h = bounds.width, bounds.height
    stroke_color = theme.component_stroke_color()
    stroke = {
        "stroke_color": stroke_color,
        "stroke_width": theme.component_stroke_width(),
    }

    channel_x = theme.MOSFET_CHANNEL_X * w
    drain_stub_x = theme.MOSFET_DRAIN_STUB_X * w
    source_stub_x = theme.MOSFET_SOURCE_STUB_X * w
    gate_y = 0.5 * h
    gate_plate_x = theme.MOSFET_GATE_PLATE_X * w
    channel_bot = theme.MOSFET_CHANNEL_INSET * h
    channel_top = h - channel_bot
    y_low, y_mid, y_high = _channel_third_centers(channel_bot, channel_top)

    segments: list[VMobject] = []

    segments.append(Line([0.0, gate_y, 0.0], [gate_plate_x, gate_y, 0.0], **stroke))

    segments.append(
        Line([gate_plate_x, channel_bot, 0.0], [gate_plate_x, channel_top, 0.0], **stroke)
    )

    if conduction_mode == "depletion":
        segments.append(
            Line([channel_x, channel_bot, 0.0], [channel_x, channel_top, 0.0], **stroke)
        )
    else:
        segments.extend(
            _enhancement_channel_thirds(
                channel_x,
                channel_bot,
                channel_top,
                stroke=stroke,
            )
        )

    if p_channel:
        source_branch_y = y_high
        drain_branch_y = y_low
        drain_pin_y = 0.0
        source_pin_y = h
        bulk_tie_y = source_branch_y
        bulk_arrow_left = False
    else:
        drain_branch_y = y_high
        source_branch_y = y_low
        drain_pin_y = h
        source_pin_y = 0.0
        bulk_tie_y = source_branch_y
        bulk_arrow_left = True

    tie_point = [source_stub_x, bulk_tie_y, 0.0]

    segments.extend(
        [
            Line([channel_x, drain_branch_y, 0.0], [drain_stub_x, drain_branch_y, 0.0], **stroke),
            Line([drain_stub_x, drain_branch_y, 0.0], [drain_stub_x, drain_pin_y, 0.0], **stroke),
            Line([channel_x, source_branch_y, 0.0], [source_stub_x, source_branch_y, 0.0], **stroke),
            Line([source_stub_x, source_branch_y, 0.0], [source_stub_x, source_pin_y, 0.0], **stroke),
            Line([channel_x, y_mid, 0.0], [source_stub_x, y_mid, 0.0], **stroke),
            Line([source_stub_x, y_mid, 0.0], tie_point, **stroke),
        ]
    )
    segments.append(
        _bulk_horizontal_arrow(
            channel_x,
            source_stub_x,
            y_mid,
            point_left=bulk_arrow_left,
            stroke=stroke,
        )
    )
    return VGroup(*segments)


def _mosfet_symbol_legacy_horizontal(
    bounds,
    *,
    p_channel: bool,
    conduction_mode: ConductionMode,
    convention: MosfetSymbolConvention,
) -> VGroup:
    """Legacy horizontal stub decoration on shared four-terminal anchors."""
    body = _mosfet_symbol_textbook_vertical(
        bounds,
        p_channel=p_channel,
        conduction_mode=conduction_mode,
    )
    w, h = bounds.width, bounds.height
    stroke = {
        "stroke_color": theme.component_stroke_color(),
        "stroke_width": theme.component_stroke_width(),
    }
    channel_x = theme.MOSFET_CHANNEL_X * w
    source_stub_x = theme.MOSFET_SOURCE_STUB_X * w
    channel_bot = theme.MOSFET_CHANNEL_INSET * h
    channel_top = h - channel_bot
    y_low, _, y_high = _channel_third_centers(channel_bot, channel_top)
    source_branch_y = y_high if p_channel else y_low
    extras: list[VMobject] = []
    if convention is MosfetSymbolConvention.arrow_on_channel:
        extras.append(_channel_side_arrow(channel_x, source_branch_y, w, stroke=stroke))
    else:
        extras.append(_source_stub_arrow(channel_x, source_branch_y, source_stub_x, stroke=stroke))
    return VGroup(body, *extras)


def _source_stub_arrow(
    channel_x: float,
    source_y: float,
    stub_x: float,
    *,
    stroke: dict,
) -> VGroup:
    """Open chevron on the source stub pointing toward the channel."""
    size = theme.MOSFET_ARROW_SIZE * max(stub_x - channel_x, 0.01)
    tip_x = channel_x + size * 0.45
    tail_x = stub_x - size * 0.12
    half = size * 0.50
    return VGroup(
        Line([tail_x, source_y + half, 0.0], [tip_x, source_y, 0.0], **stroke),
        Line([tip_x, source_y, 0.0], [tail_x, source_y - half, 0.0], **stroke),
    )


def _channel_side_arrow(
    channel_x: float,
    source_y: float,
    w: float,
    *,
    stroke: dict,
) -> VGroup:
    """Arrow chevron attached to the channel bar at source height."""
    size = theme.MOSFET_ARROW_SIZE * w
    tip_x = channel_x - size * 0.35
    heel_x = channel_x + size * 0.15
    half = size * 0.50
    return VGroup(
        Line([heel_x, source_y + half, 0.0], [tip_x, source_y, 0.0], **stroke),
        Line([tip_x, source_y, 0.0], [heel_x, source_y - half, 0.0], **stroke),
    )
