"""SignalFlow: visualize semantic propagation along routed wires."""

from __future__ import annotations

from collections.abc import Sequence

from manim import Animation, AnimationGroup, Dot, MoveAlongPath, ShowPassingFlash, VGroup, VMobject

from manim_engineering.animation import theme as anim_theme
from manim_engineering.animation.base import AnimationPlan, AnimationPrimitive
from manim_engineering.animation.layers import PROPAGATION_Z_INDEX, PULSE_Z_INDEX
from manim_engineering.animation.pacing import BEAT_DURATION
from manim_engineering.animation.purpose import AnimationPurpose
from manim_engineering.animation.registry import register_primitive
from manim_engineering.animation.wires import (
    connection_id_for_pins,
    oriented_wire_points,
    path_mobject_from_points,
    wire_path_for_connection,
    wire_path_length,
)
from manim_engineering.layout.types import LayoutResult, Point2D
from manim_engineering.renderers.minimal import theme
from manim_engineering.renderers.minimal.immutable import copy_for_animation
from manim_engineering.core.graph import CircuitGraph
from manim_engineering.semantic.propagation import PropagationRecord
from manim_engineering.semantic.signal import Signal

# Single source of truth for beat run_time is ``pacing.BEAT_DURATION``.
# A historical alias is kept for downstream code that still imports it.
DEFAULT_PROPAGATION_DURATION = BEAT_DURATION


def _pin_coord_key(point: Point2D) -> tuple[float, float]:
    return (point.x, point.y)


@register_primitive("signal_flow")
class SignalFlow(AnimationPrimitive["SignalFlow"]):
    """
    Traveling highlight along a wire path driven by propagation metadata.

    Consumes an existing :class:`PropagationRecord` (or the latest history entry).
    Does not call :meth:`Signal.propagate` and does not change graph topology.

    Topology VMobjects from the renderer are never mutated: motion paths and wire
    flashes use detached copies in ``propagation_overlays``.
    """

    purpose = AnimationPurpose.PROPAGATION

    def __init__(
        self,
        signal: Signal,
        *,
        record: PropagationRecord | None = None,
        layout: LayoutResult | None = None,
        graph: CircuitGraph | None = None,
        wire_mobjects: Sequence[VMobject] | None = None,
        duration: float = BEAT_DURATION,
    ) -> None:
        super().__init__(duration=duration)
        self._signal = signal
        self._record = record
        self._layout = layout
        self._graph = graph
        self._wire_mobjects = tuple(wire_mobjects) if wire_mobjects is not None else ()

    @property
    def signal(self) -> Signal:
        return self._signal

    def resolved_record(self) -> PropagationRecord:
        if self._record is not None:
            return self._record
        history = self._signal.propagation_history
        if not history:
            msg = "SignalFlow requires a PropagationRecord or non-empty propagation_history"
            raise ValueError(msg)
        return history[-1]

    def build(self) -> AnimationPlan:
        record = self.resolved_record()
        if self._layout is None:
            msg = "SignalFlow.build requires layout with routed wire geometry"
            raise ValueError(msg)

        connection_id = self._resolve_connection_id(record)
        wire = wire_path_for_connection(self._layout, connection_id)
        points = oriented_wire_points(
            self._layout,
            wire,
            record.from_pin_id,
            record.to_pin_id,
        )
        path = path_mobject_from_points(points)
        path.set_stroke(width=0, opacity=0)

        pulse_color = theme.color_for_signal_type(self._signal.signal_type)
        radius = theme.pulse_radius_for_wire_length(wire_path_length(points))
        pulse = Dot(radius=radius, color=pulse_color)
        # Warm gold ring around the semantic-coloured core — 3B1B style:
        # pulse keeps its semantic identity, the halo just makes it pop on
        # the dark background without the harshness of pure white. The halo
        # is a *scene-level* visual contract owned by ``animation/theme.py``,
        # not by the renderer (so it stays constant across renderer variants).
        pulse.set_stroke(anim_theme.HIGHLIGHT_COLOR, width=max(3.0, radius * 12), opacity=1.0)
        pulse.set_z_index(PULSE_Z_INDEX)
        pulse.move_to(path.point_from_proportion(0.0))

        pulse_motion = MoveAlongPath(pulse, path, run_time=self.duration)
        route_flash_anims, route_flash_overlays = self._route_flash_along_points(
            points,
            pulse_color,
        )
        wire_flash_anims, wire_flash_overlays = self._wire_flash_animations()
        flash_anims = (*route_flash_anims, *wire_flash_anims)
        flash_overlays = [*route_flash_overlays, *wire_flash_overlays]
        propagation_overlays: list[VMobject] = [path, *flash_overlays]

        if flash_anims:
            animations: tuple[Animation, ...] = (AnimationGroup(pulse_motion, *flash_anims),)
        else:
            animations = (pulse_motion,)

        return AnimationPlan(
            overlays=(pulse,),
            propagation_overlays=tuple(propagation_overlays),
            animations=animations,
            run_time=self.duration,
        )

    def play(self, scene: object) -> None:
        """Add overlay groups and play built animations on a Manim scene."""
        plan = self.build()
        add = getattr(scene, "add", None)
        play = getattr(scene, "play", None)
        if add is None or play is None:
            msg = "scene must provide add() and play() like manim.Scene"
            raise TypeError(msg)
        if plan.propagation_overlays:
            propagation = VGroup(*plan.propagation_overlays)
            propagation.set_z_index(PROPAGATION_Z_INDEX)
            add(propagation)
        add(*plan.overlays)
        play(*plan.animations, run_time=plan.run_time)

    def _resolve_connection_id(self, record: PropagationRecord) -> str:
        if self._graph is not None:
            return connection_id_for_pins(
                self._graph,
                record.from_pin_id,
                record.to_pin_id,
            )

        layout = self._layout
        assert layout is not None
        start_key = _pin_coord_key(layout.pin_positions[record.from_pin_id])
        end_key = _pin_coord_key(layout.pin_positions[record.to_pin_id])
        pin_keys = {start_key, end_key}

        for wire in layout.wires:
            if len(wire.points) < 2:
                continue
            endpoints = {
                _pin_coord_key(wire.points[0]),
                _pin_coord_key(wire.points[-1]),
            }
            if endpoints == pin_keys:
                return wire.connection_id

        if len(layout.wires) == 1:
            return layout.wires[0].connection_id

        msg = "unable to resolve connection for propagation record (pass graph=)"
        raise ValueError(msg)

    def _route_flash_along_points(
        self,
        points: Sequence[Point2D],
        pulse_color: object,
    ) -> tuple[tuple[Animation, ...], tuple[VMobject, ...]]:
        """Bright traveling flash on a detached wire copy (default visibility)."""
        if len(points) < 2:
            return (), ()
        flash_path = path_mobject_from_points(points)
        flash_path.set_stroke(
            color=pulse_color,
            width=theme.WIRE_STROKE_WIDTH * 2.5,
            opacity=1.0,
        )
        flash_target = copy_for_animation(flash_path)
        flash_target.set_z_index(PROPAGATION_Z_INDEX)
        return (
            (
                ShowPassingFlash(
                    flash_target,
                    time_width=0.55,
                    run_time=self.duration,
                ),
            ),
            (flash_target,),
        )

    def _wire_flash_animations(self) -> tuple[tuple[Animation, ...], tuple[VMobject, ...]]:
        if not self._wire_mobjects:
            return (), ()
        animations: list[Animation] = []
        overlays: list[VMobject] = []
        for line in self._wire_mobjects:
            flash_target = copy_for_animation(line)
            flash_target.set_z_index(PROPAGATION_Z_INDEX)
            overlays.append(flash_target)
            animations.append(
                ShowPassingFlash(flash_target, time_width=0.35, run_time=self.duration)
            )
        return tuple(animations), tuple(overlays)
