"""Scene parameter inspector: walk the mobject tree and report positions/sizes.

Usage::

    from manim_engineering.debug import SceneInspector
    inspector = SceneInspector(scene)
    inspector.print_tree()        # print to stdout
    data = inspector.as_dict()    # export as JSON-serializable dict
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from manim import Mobject, Scene


class SceneInspector:
    """Print or export a structured view of every mobject in a Manim scene."""

    def __init__(self, scene: Scene) -> None:
        self._scene = scene

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict of the scene mobject tree."""
        items: list[dict[str, Any]] = []
        for i, mob in enumerate(self._scene.mobjects):
            items.append(self._walk(mob, i))
        return {"scene": type(self._scene).__name__, "objects": items}

    def print_tree(self) -> None:
        """Print the mobject tree to stdout."""
        for i, mob in enumerate(self._scene.mobjects):
            self._print_mob(mob, depth=0, prefix=f"[{i}]")

    def dump_json(self, path: str | None = None) -> str:
        """Serialize the tree to JSON and optionally write to a file. Returns the JSON string."""
        data = self.as_dict()
        text = json.dumps(data, indent=2)
        if path is not None:
            with open(path, "w") as f:
                f.write(text)
            f.close()
        return text

    def _walk(self, mob: Mobject, index: int) -> dict[str, Any]:
        bbox = None
        pos = None
        try:
            b = mob.get_bounding_box()
            if b is not None:
                bbox = [float(b[0]), float(b[1]), float(b[2]), float(b[3])]
        except Exception:
            pass
        try:
            c = mob.get_center()
            if c is not None:
                pos = [float(c[0]), float(c[1]), float(c[2])]
        except Exception:
            pass
        node: dict[str, Any] = {
            "index": index,
            "type": type(mob).__name__,
        }
        if bbox is not None:
            node["bounds"] = bbox
        if pos is not None:
            node["center"] = pos
        if hasattr(mob, "z_index"):
            node["z_index"] = getattr(mob, "z_index")
        subs = getattr(mob, "submobjects", None)
        if subs:
            node["children"] = [self._walk(child, j) for j, child in enumerate(subs)]
        return node

    def _print_mob(self, mob: object, depth: int = 0, prefix: str = "") -> None:
        indent = "  " * depth
        tname = type(mob).__name__
        try:
            c = mob.get_center()
            info = f"center=({c[0]:.2f},{c[1]:.2f})"
        except Exception:
            info = "(no center)"
        z = getattr(mob, "z_index", "?")
        print(f"{indent}{prefix} {tname} {info} z={z}")
        for j, sub in enumerate(getattr(mob, "submobjects", [])):
            self._print_mob(sub, depth + 1, f"[{j}]")
