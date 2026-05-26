"""Shared utilities for waveform teaching demos (re-exports + demo-only helpers).

:class:`WaveformDemoScene` and :class:`WaveformFixture` live in
``manim_engineering.animation.teaching_scene``; this module re-exports them
for examples that add ``examples/`` to ``sys.path`` and import ``_shared``
by bare name.

Demo-only :func:`capture_camera_frame` stays here (not installed package API).
"""

from __future__ import annotations

from pathlib import Path

from manim import Scene

from manim_engineering.animation.hud import CaptionTrack
from manim_engineering.animation.teaching_scene import WaveformDemoScene, WaveformFixture

__all__ = [
    "CaptionTrack",
    "WaveformDemoScene",
    "WaveformFixture",
    "capture_camera_frame",
]


def capture_camera_frame(scene: Scene, path: Path) -> None:
    """Save the current camera image to ``path`` (PNG).

    Demo-only helper. Kept module-level (not on the base class) so demos
    that have no acceptance-frame requirement are not coupled to PIL.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = scene.camera.get_image()
    if hasattr(frame, "save"):
        frame.save(path)
        return
    import numpy as np
    from PIL import Image

    Image.fromarray(np.asarray(frame)).save(path)
