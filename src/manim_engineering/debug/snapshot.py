"""Frame snapshot and topology dump tools for visual debugging.

Activate with ``DEBUG_SNAPSHOT=1`` to save per-stage PNG frames and JSON
bounding-box dumps during scene construction. Call ``snapshot_frame(scene, label)``
at any pipeline checkpoint (post-layout, post-render, post-animation).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from manim import Mobject, Scene


DEBUG_OUTPUT_DIR = Path(os.environ.get("DEBUG_SNAPSHOT_DIR", "media/debug"))


def _ensure_output_dir(scene: object) -> Path:
    scene_name = getattr(scene, "__class__", type(scene)).__name__
    target = DEBUG_OUTPUT_DIR / scene_name
    target.mkdir(parents=True, exist_ok=True)
    return target


def snapshot_frame(scene: Scene, label: str) -> Path | None:
    """Save a PNG of the current camera frame with a descriptive label.

    Returns the output path, or None if ``DEBUG_SNAPSHOT`` is not set.
    """
    if os.environ.get("DEBUG_SNAPSHOT", "") != "1":
        return None
    target = _ensure_output_dir(scene)
    path = target / f"{label}.png"
    scene.camera.get_image().save(str(path))
    return path


def _mobject_bounds(mob: Mobject) -> list[float] | None:
    """Get axis-aligned bounding box [x0, y0, x1, y1] or None."""
    try:
        bbox_pts = mob.get_bounding_box()
        min_corner, max_corner = bbox_pts[0], bbox_pts[2]
        return [
            float(min_corner[0]),
            float(min_corner[1]),
            float(max_corner[0]),
            float(max_corner[1]),
        ]
    except Exception:
        return None


def snapshot_topology(scene: Scene, label: str) -> dict[str, Any] | None:
    """Dump JSON bounds for every mobject in the scene with the given label.

    Returns the dict, or None if ``DEBUG_SNAPSHOT`` is not set.
    """
    if os.environ.get("DEBUG_SNAPSHOT", "") != "1":
        return None
    target = _ensure_output_dir(scene)
    path = target / f"{label}.json"
    items: list[dict[str, Any]] = []
    for i, mob in enumerate(scene.mobjects):
        bbox = _mobject_bounds(mob)
        if bbox is None:
            continue
        items.append({
            "index": i,
            "type": type(mob).__name__,
            "bounds": bbox,
            "z_index": getattr(mob, "z_index", None),
        })
    dump = {"label": label, "objects": items}
    path.write_text(json.dumps(dump, indent=2))
    return dump
