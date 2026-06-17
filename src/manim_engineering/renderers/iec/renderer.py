"""IEC renderer family backed by the stable minimal projection pipeline."""

from __future__ import annotations

from collections.abc import Mapping

from manim import Line, Rectangle, VGroup

from manim_engineering.components import Resistor
from manim_engineering.components.element import CircuitElement
from manim_engineering.core.graph import CircuitGraph
from manim_engineering.layout.types import LayoutResult
from manim_engineering.renderers.iec import theme
from manim_engineering.renderers.minimal.conventions import MosfetSymbolConvention
from manim_engineering.renderers.minimal.immutable import TopologyProjection, topology_from_render
from manim_engineering.renderers.minimal.renderer import MinimalRenderer


class IECRenderer(MinimalRenderer):
    """IEC-facing renderer variant.

    This vertical slice establishes the renderer-family API and selects a
    convention-owned symbol style without duplicating topology, layout, or
    semantic behavior.
    """

    def __init__(self) -> None:
        super().__init__(mosfet_convention=MosfetSymbolConvention.arrow_on_channel)

    def _resistor_symbol(self, component: Resistor) -> VGroup:
        """IEC resistor: rectangular body with straight leads."""
        bounds = component.get_bounds()
        w, h = bounds.width, bounds.height
        y = h * 0.5
        lead_left = 0.22 * w
        lead_right = 0.78 * w
        body_width = lead_right - lead_left
        body_height = 0.46 * h
        stroke = {
            "stroke_color": theme.component_stroke_color(),
            "stroke_width": theme.component_stroke_width(),
        }
        body = Rectangle(
            width=body_width,
            height=body_height,
            fill_opacity=0.0,
            **stroke,
        )
        body.move_to([w * 0.5, y, 0.0])
        return VGroup(
            Line([0.0, y, 0.0], [lead_left, y, 0.0], **stroke),
            body,
            Line([lead_right, y, 0.0], [w, y, 0.0], **stroke),
        )


class IECManimRenderer:
    """Adapter matching :class:`ManimRenderer` for IEC topology projection."""

    def __init__(self) -> None:
        self._inner = IECRenderer()

    def render(
        self,
        circuit: CircuitGraph,
        layout: LayoutResult,
        elements: Mapping[str, CircuitElement],
    ) -> VGroup:
        """Project circuit topology and layout into a static scene group."""
        return self._inner.render_circuit(circuit, layout, elements)

    def render_topology(
        self,
        circuit: CircuitGraph,
        layout: LayoutResult,
        elements: Mapping[str, CircuitElement],
    ) -> TopologyProjection:
        """Project circuit topology into immutable component and wire groups."""
        return topology_from_render(self.render(circuit, layout, elements), layout)

    def render_circuit(
        self,
        circuit: CircuitGraph,
        layout: LayoutResult,
        elements: Mapping[str, CircuitElement],
    ) -> VGroup:
        """Alias for :meth:`render`."""
        return self.render(circuit, layout, elements)
