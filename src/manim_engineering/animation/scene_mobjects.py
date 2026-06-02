"""Helpers for collecting the displayed mobjects of a scene."""

from __future__ import annotations

from manim.utils.iterables import list_update


def scene_display_mobjects(scene: object) -> list[object]:
    """Mobjects that Manim's Cairo renderer treats as displayed scene content."""
    mobjects = list(getattr(scene, "mobjects", ()))
    foreground = list(getattr(scene, "foreground_mobjects", ()))
    return list_update(mobjects, foreground)
