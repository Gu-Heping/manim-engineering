"""Coordinate overlay mixin for inspecting scene geometry.

Add to any Manim Scene to see bounding boxes, anchor points, and z-index
labels on every mobject. Toggle with ``DEBUG_COORD_OVERLAY=1``.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from manim import WHITE, YELLOW, Rectangle, Text, VMobject

if TYPE_CHECKING:
    pass


class SceneCoordinateOverlay:
    """Mixin: draws debug bounding boxes, anchors, and z-index labels.

    Apply to a Manim Scene subclass::

        class MyScene(SceneCoordinateOverlay, Scene):
            def construct(self):
                # normal scene code; overlay is drawn after each play()
    """

    def _debug_overlay_labels(self) -> VMobject:
        """Return a VGroup of debug rectangles, dots, and text for the current scene."""
        group: list[VMobject] = []
        for i, mob in enumerate(self.mobjects):
            if isinstance(mob, VMobject):
                group.extend(self._debug_subtree(mob, prefix=str(i)))
        from manim import VGroup

        return VGroup(*group)

    def _debug_subtree(self, root: VMobject, prefix: str) -> list[VMobject]:
        result: list[VMobject] = []
        try:
            rect = root.get_bounding_box()
        except Exception:
            return result
        if rect is None:
            return result
        rect_mob = Rectangle(
            width=rect[2] - rect[0],
            height=rect[3] - rect[1],
            stroke_color=YELLOW,
            stroke_width=0.5,
            fill_opacity=0,
        )
        rect_mob.move_to([(rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2, 0.0])

        label = Text(
            f"{prefix} z={getattr(root, 'z_index', 0)}",
            font_size=12,
            color=WHITE,
        )
        label.move_to([rect[0], rect[3], 0.0])
        result.extend([rect_mob, label])

        for j, sub in enumerate(getattr(root, "submobjects", [])):
            if isinstance(sub, VMobject):
                result.extend(self._debug_subtree(sub, f"{prefix}.{j}"))

        return result

    def play(self, *args, **kwargs):
        result = super().play(*args, **kwargs)
        if os.environ.get("DEBUG_COORD_OVERLAY", "") == "1":
            overlay = self._debug_overlay_labels()
            self.add(overlay)
            self.wait(0.01)
            self.remove(overlay)
        return result
