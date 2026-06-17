"""Immutable topology projection for animation handoff."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from manim import VGroup, VMobject

from manim_engineering.layout.types import LayoutResult

_SEMANTIC_METADATA_KEYS = ("element_id", "connection_id")


def _copy_semantic_metadata(source: VMobject, target: VMobject) -> VMobject:
    for key in _SEMANTIC_METADATA_KEYS:
        if hasattr(source, key):
            setattr(target, key, getattr(source, key))
    return target


def _detach_points(mob: VMobject) -> VMobject:
    """Return a copy whose point arrays are independent of the source."""
    copy = mob.copy()
    points = np.array(mob.get_all_points(), dtype=float)
    if len(points) > 0:
        copy.set_points(points.copy())
    return _copy_semantic_metadata(mob, copy)


def copy_for_animation(mob: VMobject) -> VMobject:
    """
    Deep-copy a VMobject tree for transient animation overlays.

    Animation must never pass renderer topology instances to ``ShowPassingFlash``,
    ``MoveAlongPath`` paths that alias wire geometry, or other mutating primitives.
    """
    if isinstance(mob, VGroup):
        return _copy_semantic_metadata(
            mob,
            VGroup(*(_detach_points(sub) for sub in mob.submobjects)),
        )
    return _detach_points(mob)


@dataclass(frozen=True)
class TopologyProjection:
    """
    Read-only circuit topology after ``ManimRenderer`` projection.

    ``components`` and ``wires`` are independent copies; animation overlays must not
    mutate these groups or their submobjects.
    """

    components: VGroup
    wires: VGroup
    n_components: int

    @property
    def circuit_group(self) -> VGroup:
        """Components then wires (back → front), for scene ``add``."""
        return VGroup(self.components, self.wires)

    def wire_lines(self) -> tuple[VMobject, ...]:
        """Flat wire segment lines (copies are not required for read-only tests)."""
        lines: list[VMobject] = []
        for sub in self.wires.submobjects:
            if isinstance(sub, VMobject) and not isinstance(sub, VGroup):
                lines.append(sub)
            elif isinstance(sub, VGroup):
                lines.extend(sub.submobjects)
        return tuple(lines)


def topology_from_render(
    rendered: VGroup,
    layout_result: LayoutResult,
) -> TopologyProjection:
    """Split a rendered circuit group into immutable component and wire groups."""
    n = len(layout_result.placements)
    component_slice = rendered.submobjects[:n]
    wire_slice = rendered.submobjects[n:]
    return TopologyProjection(
        components=VGroup(*(copy_for_animation(m) for m in component_slice)),
        wires=VGroup(*(copy_for_animation(m) for m in wire_slice)),
        n_components=n,
    )
