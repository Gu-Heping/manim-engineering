"""Shared Manim Text helpers for the minimal renderer."""

from __future__ import annotations

from typing import Literal

import numpy as np
from manim import ManimColor, Mobject, Text, VMobject

# Nets are pushed below component bodies; glyph paths must stay on top at pin rows.
WIRE_Z_INDEX = -1
LABEL_Z_INDEX = 1

_ME_LABEL_COLOR_ATTR = "_me_label_color"

LabelRefreshMode = Literal["full", "stroke_only"]


def _label_color(mob: Mobject) -> ManimColor | None:
    stored = getattr(mob, _ME_LABEL_COLOR_ATTR, None)
    if stored is not None:
        return ManimColor(stored)
    return None


def is_label_root(mob: Mobject) -> bool:
    """True when ``mob`` was created by :func:`label_text`."""
    return _label_color(mob) is not None


def iter_label_roots(root: Mobject) -> tuple[Mobject, ...]:
    """Every ``label_text`` root under ``root`` (deduplicated by identity)."""
    seen: set[int] = set()
    roots: list[Mobject] = []
    for mob in root.get_family():
        if not is_label_root(mob):
            continue
        sid = id(mob)
        if sid in seen:
            continue
        seen.add(sid)
        roots.append(mob)
    return tuple(roots)


def hide_labels(root: Mobject) -> None:
    """Set label roots to invisible (intro: fade bodies without animating glyphs)."""
    for mob in iter_label_roots(root):
        mob.set_opacity(0.0)


def show_labels(root: Mobject) -> None:
    """Reveal label roots and restore fill/stroke after a body-only fade."""
    for mob in iter_label_roots(root):
        mob.set_opacity(1.0)
    refresh_label_strokes(root, mode="full")


def _apply_label_glyph_style(
    mob: Mobject,
    color: ManimColor,
    *,
    stroke_only: bool = False,
) -> None:
    """Restore one Text glyph (or container) after parent opacity animations."""
    transparent = np.array([*color.to_rgb(), 0.0], dtype=float)
    if not stroke_only:
        mob.set_fill(color, opacity=1.0)
    mob.set_stroke(color=color, width=0, opacity=0)
    if hasattr(mob, "set_background_stroke"):
        mob.set_background_stroke(color=color, width=0, opacity=0)
    if len(mob.points) == 0:
        mob.set_z_index(LABEL_Z_INDEX)
        return
    stroke_rgbas = getattr(mob, "stroke_rgbas", None)
    if stroke_rgbas is not None and len(stroke_rgbas):
        stroke_rgbas[:] = transparent
    mob.set_z_index(LABEL_Z_INDEX)


def refresh_label_strokes(root: Mobject, *, mode: LabelRefreshMode = "full") -> None:
    """Re-apply label styling after ``set_opacity`` / ``FadeIn`` on a parent.

    ``full`` restores fill and zeroes stroke (after restore or intro reveal).
    ``stroke_only`` zeroes corrupted glyph strokes without forcing fill opacity
    to 1.0 — use after :func:`dim_topology` so labels dim with the symbol bodies.
    """
    stroke_only = mode == "stroke_only"
    touched: set[int] = set()
    for mob in root.get_family():
        color = _label_color(mob)
        if color is None:
            continue
        for sub in mob.get_family():
            sid = id(sub)
            if sid in touched:
                continue
            touched.add(sid)
            _apply_label_glyph_style(sub, color, stroke_only=stroke_only)

    if stroke_only:
        return

    for mob in root.get_family():
        if id(mob) in touched:
            continue
        if len(mob.points) == 0:
            mob.set_stroke(width=0, opacity=0)


def label_text(
    string: str,
    *,
    font_size: float,
    color: object,
    font: str | None = None,
) -> Text:
    """Colored label with no visible glyph stroke; draws above wire segments."""
    kwargs: dict = {"font_size": font_size, "color": color}
    if font:
        kwargs["font"] = font
    label = Text(string, **kwargs)
    setattr(label, _ME_LABEL_COLOR_ATTR, ManimColor(color))
    refresh_label_strokes(label)
    return label
