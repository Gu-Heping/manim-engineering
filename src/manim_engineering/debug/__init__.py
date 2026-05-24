"""Visual debugging tools for scene geometry and layout inspection.

Dev-only package: do not import from core/semantic/components/layout/protocol/
waveform layers. These helpers are for scene/renderer inspection workflows.

Activate via environment variables:

- ``DEBUG_COORD_OVERLAY=1`` — draw bounding boxes and anchor points on every mobject
- ``DEBUG_SNAPSHOT=1`` — save per-stage PNG frames and JSON bounds
- ``DEBUG_RENDERER=1`` — show component bounds rects and anchors in symbol renderer

Usage::

    import os
    os.environ["DEBUG_COORD_OVERLAY"] = "1"
    from manim_engineering.debug import SceneCoordinateOverlay
"""

from manim_engineering.debug.coord_overlay import SceneCoordinateOverlay
from manim_engineering.debug.inspector import SceneInspector
from manim_engineering.debug.snapshot import snapshot_frame, snapshot_topology

__all__ = [
    "SceneCoordinateOverlay",
    "SceneInspector",
    "snapshot_frame",
    "snapshot_topology",
]
