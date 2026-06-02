"""Small tracing helpers for scene-stage animation tests."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from manim import AnimationGroup, Group, LaggedStart

from manim_engineering.animation.scene_mobjects import scene_display_mobjects
from manim_engineering.renderers.minimal.labels import iter_label_roots, label_role, label_visible


def animation_roles(animation: object) -> list[str]:
    """Collect label roles reachable from one animation tree."""
    roles: list[str] = []
    mob = getattr(animation, "mobject", None)
    if mob is not None:
        role = label_role(mob)
        if role is not None:
            roles.append(role)
    if isinstance(animation, (LaggedStart, AnimationGroup)):
        for child in animation.animations:
            roles.extend(animation_roles(child))
    return roles


def played_role_sets(
    played: Iterable[tuple[tuple[object, ...], dict] | tuple[object, ...]],
) -> list[set[str]]:
    """Role sets referenced by each recorded ``scene.play(...)`` call."""

    def _animations(
        entry: tuple[tuple[object, ...], dict] | tuple[object, ...],
    ) -> tuple[object, ...]:
        if (
            len(entry) == 2
            and isinstance(entry[0], tuple)
            and isinstance(entry[1], dict)
        ):
            return entry[0]
        return entry

    return [
        {role for anim in _animations(entry) for role in animation_roles(anim)}
        for entry in played
    ]


def scene_visible_label_texts(
    scene: object,
    *,
    roles: tuple[str, ...] | None = None,
) -> set[str]:
    """Visible label texts currently attached to a scene-like object's mobjects."""
    root = Group(*scene_display_mobjects(scene))
    return {
        label.text
        for label in iter_label_roots(root, roles=roles)
        if label_visible(label)
    }


def trace_stage_names(path: Path) -> list[str]:
    """Stage names from one flushed animation trace JSON file."""
    payload = trace_payload(path)
    return [entry["stage"] for entry in payload["stages"]]


def trace_payload(path: Path) -> dict[str, object]:
    """Decoded payload from one flushed animation trace JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def trace_stage_entries(path: Path, stage: str | None = None) -> list[dict[str, object]]:
    """Trace stage entries, optionally filtered by stage name."""
    entries = list(trace_payload(path)["stages"])
    if stage is None:
        return entries
    return [entry for entry in entries if entry["stage"] == stage]
