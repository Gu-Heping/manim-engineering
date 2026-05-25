"""Helpers for configuring a Manim Scene around a waveform-aware layout.

Centralises camera framing so example scenes do not each invent their own
combination of ``scene_frame_bounds`` / ``frame_size_for_pixel_aspect`` /
``camera_frame_center``. Without this helper, every example wires the same
~25 lines of boilerplate and is one ``content.get_center()`` away from a
mis-framed video.

Lives in the animation layer (not waveform) because waveform must remain
Manim-free; this module is where layout/waveform math meets ``self.camera``.
"""

from __future__ import annotations

from dataclasses import dataclass

from manim_engineering.animation import theme as anim_theme
from manim_engineering.layout.types import LayoutResult
from manim_engineering.waveform.layout import (
    WaveformPanelSpec,
    camera_frame_center,
    frame_size_for_pixel_aspect,
    scene_frame_bounds,
)
from manim_engineering.waveform.trace import WaveformBundle

TOPOLOGY_CAMERA_PADDING = 0.5
"""Default world-space padding applied around layout.scene_bbox for topology framing.

Matches the ``padding`` constant in :func:`scene_frame_bounds` so topology-only
scenes (no waveform panel) share the same breathing-room around the layout.
"""


@dataclass(frozen=True)
class SceneCamera:
    """Resolved camera parameters for a waveform scene."""

    frame_width: float
    frame_height: float
    frame_cx: float
    frame_cy: float


def resolve_scene_camera(
    layout: LayoutResult,
    panel_spec: WaveformPanelSpec,
    bundle: WaveformBundle,
    *,
    pixel_width: int,
    pixel_height: int,
    target_fill: float = 0.70,
    min_width: float = 4.0,
    min_height: float = 2.5,
    subtitle_band: float = 0.0,
) -> SceneCamera:
    """Compute the frame size, aspect-corrected dimensions, and center.

    ``subtitle_band`` reserves extra world-Y above the content so HUD text can
    sit outside the circuit/waveform region. The center is shifted up by half
    the band so the topology stays visually centered.
    """
    frame_w, frame_h = scene_frame_bounds(
        layout,
        panel_spec,
        trace_count=len(bundle.traces),
        target_fill=target_fill,
    )
    frame_w, frame_h = frame_size_for_pixel_aspect(
        max(min_width, frame_w),
        max(min_height, frame_h + subtitle_band),
        pixel_width=pixel_width,
        pixel_height=pixel_height,
    )
    frame_cx, frame_cy = camera_frame_center(
        layout,
        panel_spec,
        trace_count=len(bundle.traces),
    )
    frame_cy += subtitle_band / 2
    return SceneCamera(
        frame_width=frame_w,
        frame_height=frame_h,
        frame_cx=frame_cx,
        frame_cy=frame_cy,
    )


def configure_waveform_scene_camera(
    scene: object,
    layout: LayoutResult,
    panel_spec: WaveformPanelSpec,
    bundle: WaveformBundle,
    *,
    target_fill: float = 0.70,
    min_width: float = 4.0,
    min_height: float = 2.5,
    subtitle_band: float = 0.0,
    write_global_config: bool = False,
    apply_background: bool = True,
    background_color: str = anim_theme.DEFAULT_BACKGROUND,
) -> SceneCamera:
    """Apply :func:`resolve_scene_camera` to ``scene.camera``.

    Uses ``manim.config.pixel_width``/``pixel_height`` for the output aspect
    and writes ``self.camera.frame_width/height/center`` so subsequent
    rendering uses the corrected frame.

    ``write_global_config`` (default ``False``) controls whether
    ``manim.config.frame_width``/``frame_height`` are also mutated. Set
    ``True`` from CLI entry points that need ``config`` to reflect the
    chosen frame for downstream consumers; leave ``False`` from tests and
    from any ``tempconfig`` context so multi-scene runs do not bleed frame
    sizes into each other.

    ``apply_background`` (default ``True``) sets the scene background to the
    3B1B dark blue (``#1e1e2e``) instead of Manim's harsh pure-black default.
    Pass ``False`` only if a scene already owns its background colour.
    """
    from manim import config

    camera = resolve_scene_camera(
        layout,
        panel_spec,
        bundle,
        pixel_width=config.pixel_width,
        pixel_height=config.pixel_height,
        target_fill=target_fill,
        min_width=min_width,
        min_height=min_height,
        subtitle_band=subtitle_band,
    )

    if write_global_config:
        config.frame_width = camera.frame_width
        config.frame_height = camera.frame_height
    scene.camera.frame_width = camera.frame_width
    scene.camera.frame_height = camera.frame_height
    scene.camera.frame_center = [camera.frame_cx, camera.frame_cy]
    if apply_background:
        scene.camera.background_color = background_color
    return camera


def resolve_topology_scene_camera(
    layout: LayoutResult,
    *,
    pixel_width: int,
    pixel_height: int,
    target_fill: float = 0.70,
    min_width: float = 4.0,
    min_height: float = 2.5,
    subtitle_band: float = 0.0,
    padding: float = TOPOLOGY_CAMERA_PADDING,
) -> SceneCamera:
    """Compute camera params for a topology-only scene (no waveform panel).

    Mirrors :func:`resolve_scene_camera` but operates purely on
    ``layout.scene_bbox`` so analog/digital diagrams without timing traces can
    frame themselves without inventing a stub :class:`WaveformPanelSpec`.

    ``subtitle_band`` reserves extra world-Y above the content so HUD captions
    sit outside the layout region; the center is shifted up by half the band
    so the topology stays visually centered.
    """
    if not 0.0 < target_fill <= 1.0:
        msg = f"target_fill must be in (0, 1], got {target_fill}"
        raise ValueError(msg)
    scene = layout.scene_bbox
    content_w = scene.width / target_fill
    content_h = scene.height / target_fill
    frame_w = content_w + 2 * padding
    frame_h = content_h + 2 * padding + subtitle_band
    frame_w, frame_h = frame_size_for_pixel_aspect(
        max(min_width, frame_w),
        max(min_height, frame_h),
        pixel_width=pixel_width,
        pixel_height=pixel_height,
    )
    frame_cx = (scene.min_x + scene.max_x) * 0.5
    frame_cy = (scene.min_y + scene.max_y) * 0.5 + subtitle_band * 0.5
    return SceneCamera(
        frame_width=frame_w,
        frame_height=frame_h,
        frame_cx=frame_cx,
        frame_cy=frame_cy,
    )


def configure_topology_scene_camera(
    scene: object,
    layout: LayoutResult,
    *,
    target_fill: float = 0.70,
    min_width: float = 4.0,
    min_height: float = 2.5,
    subtitle_band: float = 0.0,
    padding: float = TOPOLOGY_CAMERA_PADDING,
    write_global_config: bool = False,
    apply_background: bool = True,
    background_color: str = anim_theme.DEFAULT_BACKGROUND,
) -> SceneCamera:
    """Apply :func:`resolve_topology_scene_camera` to ``scene.camera``.

    Equivalent of :func:`configure_waveform_scene_camera` for topology-only
    scenes. Uses ``manim.config.pixel_width``/``pixel_height`` for the output
    aspect and writes ``self.camera.frame_width/height/center`` so subsequent
    rendering uses the corrected frame.

    See :func:`configure_waveform_scene_camera` for the ``write_global_config``
    and ``apply_background`` semantics (identical here).
    """
    from manim import config

    camera = resolve_topology_scene_camera(
        layout,
        pixel_width=config.pixel_width,
        pixel_height=config.pixel_height,
        target_fill=target_fill,
        min_width=min_width,
        min_height=min_height,
        subtitle_band=subtitle_band,
        padding=padding,
    )

    if write_global_config:
        config.frame_width = camera.frame_width
        config.frame_height = camera.frame_height
    scene.camera.frame_width = camera.frame_width
    scene.camera.frame_height = camera.frame_height
    scene.camera.frame_center = [camera.frame_cx, camera.frame_cy]
    if apply_background:
        scene.camera.background_color = background_color
    return camera
