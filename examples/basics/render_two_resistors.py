"""
Build two resistors, layout, and render with MinimalRenderer.

Requires manim: ``pip install -e ".[manim]"``

Optional preview: ``manim -pql examples/basics/render_two_resistors.py RenderTwoResistors``
"""

from __future__ import annotations

from manim_engineering.components import Resistor
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import MinimalRenderer
from manim_engineering.semantic import CircuitGraph


def build_scene_mobject():
    """Return a static VGroup for the two-resistor fixture (no Scene required)."""
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))

    layout = LayoutEngine().layout(graph, {"r1": r1, "r2": r2})
    return MinimalRenderer().render_layout(layout, graph, {"r1": r1, "r2": r2})


def main() -> None:
    mob = build_scene_mobject()
    print(f"rendered group with {len(mob.submobjects)} top-level submobjects")


if __name__ == "__main__":
    main()


try:
    from manim import Scene

    class RenderTwoResistors(Scene):
        """Optional Manim scene entry for local preview."""

        def construct(self) -> None:
            self.add(build_scene_mobject())

except ImportError:
    pass
