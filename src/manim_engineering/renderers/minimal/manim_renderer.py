"""ManimRenderer: adapter alias for the minimal Manim projection pipeline."""

from __future__ import annotations

from collections.abc import Mapping

from manim import VGroup

from manim_engineering.components.element import CircuitElement
from manim_engineering.core.graph import CircuitGraph
from manim_engineering.layout.types import LayoutResult
from manim_engineering.renderers.minimal.immutable import TopologyProjection, topology_from_render
from manim_engineering.renderers.minimal.conventions import MosfetSymbolConvention
from manim_engineering.renderers.minimal.renderer import MinimalRenderer


class ManimRenderer:
    """
    Render adapter: graph + layout → Manim ``VGroup``.

    Delegates to :class:`MinimalRenderer`; layout must come from :meth:`LayoutEngine.solve`.
    """

    def __init__(
        self,
        *,
        mosfet_convention: MosfetSymbolConvention | None = None,
    ) -> None:
        self._inner = MinimalRenderer(mosfet_convention=mosfet_convention)

    def render(
        self,
        circuit: CircuitGraph,
        layout: LayoutResult,
        elements: Mapping[str, CircuitElement],
    ) -> VGroup:
        """
        Project circuit topology and layout into a static scene group.

        Child order matches :meth:`MinimalRenderer.render_layout`: components, then wires.
        Overlay waveform panels after wires in scene ``construct``.
        """
        return self._inner.render_circuit(circuit, layout, elements)

    def render_topology(
        self,
        circuit: CircuitGraph,
        layout: LayoutResult,
        elements: Mapping[str, CircuitElement],
    ) -> TopologyProjection:
        """
        Project circuit topology into immutable component and wire groups.

        Animation receives read-only references; use overlay copies for motion paths
        and ``ShowPassingFlash`` targets.
        """
        rendered = self.render(circuit, layout, elements)
        return topology_from_render(rendered, layout)

    def render_circuit(
        self,
        circuit: CircuitGraph,
        layout: LayoutResult,
        elements: Mapping[str, CircuitElement],
    ) -> VGroup:
        """Alias for :meth:`render`."""
        return self.render(circuit, layout, elements)
