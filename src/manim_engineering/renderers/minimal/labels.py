"""Shared Manim Text helpers for the minimal renderer."""

from __future__ import annotations

from typing import Literal

import numpy as np
from manim import ManimColor, Mobject, Text

# Nets are pushed below component bodies; glyph paths must stay on top at pin rows.
WIRE_Z_INDEX = -1
LABEL_Z_INDEX = 1

_ME_LABEL_COLOR_ATTR = "_me_label_color"
_ME_LABEL_ROLE_ATTR = "_me_label_role"

LabelRefreshMode = Literal["full", "stroke_only"]


def _label_color(mob: Mobject) -> ManimColor | None:
    stored = getattr(mob, _ME_LABEL_COLOR_ATTR, None)
    if stored is not None:
        return ManimColor(stored)
    return None


def is_label_root(mob: Mobject) -> bool:
    """True when ``mob`` was created by :func:`label_text`."""
    return _label_color(mob) is not None


def label_role(mob: Mobject) -> str | None:
    """Optional semantic role set by :func:`label_text` (for placement overrides)."""
    role = getattr(mob, _ME_LABEL_ROLE_ATTR, None)
    return role if isinstance(role, str) else None


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


def _label_subtree_ids(root: Mobject) -> set[int]:
    ids: set[int] = set()
    for label_root in iter_label_roots(root):
        for sub in label_root.get_family():
            ids.add(id(sub))
    return ids


def normalize_stroke_only_geometry(root: Mobject) -> None:
    """Clear accidental fill on symbol/wire ``Line`` objects after parent ``set_opacity``.

    Manim ``Line`` defaults to white fill at opacity 0; a parent ``set_opacity(1.0)``
    (intro restore, dim/restore) promotes that fill and paints zig-zag resistors solid.
    """
    label_ids = _label_subtree_ids(root)
    for mob in root.get_family():
        if id(mob) in label_ids:
            continue
        if mob.__class__.__name__ != "Line" or len(mob.points) == 0:
            continue
        mob.set_fill(opacity=0.0, family=False)


def iter_symbol_strokes(root: Mobject) -> tuple[Mobject, ...]:
    """Return drawable symbol/wire bodies for intro ``Create`` (excludes label subtrees)."""
    label_ids = _label_subtree_ids(root)
    seen: set[int] = set()
    strokes: list[Mobject] = []
    for mob in root.get_family():
        sid = id(mob)
        if sid in label_ids or sid in seen or len(mob.points) == 0:
            continue
        name = mob.__class__.__name__
        if name in ("Line", "Polygon", "Dot"):
            seen.add(sid)
            strokes.append(mob)
    return tuple(strokes)


def partition_symbol_strokes(
    strokes: tuple[Mobject, ...],
) -> tuple[tuple[Mobject, ...], tuple[Mobject, ...]]:
    """Split intro strokes into line-only bodies and filled bodies (Polygon/Dot)."""
    line_strokes: list[Mobject] = []
    filled_strokes: list[Mobject] = []
    for mob in strokes:
        if mob.__class__.__name__ == "Line":
            line_strokes.append(mob)
        elif mob.__class__.__name__ in ("Polygon", "Dot"):
            filled_strokes.append(mob)
    return tuple(line_strokes), tuple(filled_strokes)


def prepare_stroke_reveal(mobjects: tuple[Mobject, ...]) -> None:
    """Hide symbol strokes/fills before ``Create`` without touching label subtrees."""
    for mob in mobjects:
        mob.set_stroke(opacity=0.0, family=False)
        if mob.__class__.__name__ != "Line":
            mob.set_fill(opacity=0.0, family=False)
        else:
            mob.set_fill(opacity=0.0, family=False)


def apply_symbol_opacity(root: Mobject, opacity: float) -> None:
    """Dim or restore symbol geometry via stroke/fill opacity (never ``VGroup.set_opacity``)."""
    label_ids = _label_subtree_ids(root)
    for mob in root.get_family():
        if id(mob) in label_ids or len(mob.points) == 0:
            continue
        name = mob.__class__.__name__
        if name == "Line":
            mob.set_stroke(opacity=opacity, family=False)
            mob.set_fill(opacity=0.0, family=False)
        elif name in ("Polygon", "Dot"):
            mob.set_stroke(opacity=opacity, family=False)
            mob.set_fill(opacity=opacity, family=False)
        elif mob.get_stroke_width() > 0:
            mob.set_stroke(opacity=opacity, family=False)
        elif mob.get_fill_opacity() > 0:
            mob.set_fill(opacity=opacity, family=False)


def apply_label_opacity(root: Mobject, opacity: float) -> None:
    """Dim or restore label roots without touching symbol ``Line`` geometry."""
    for mob in iter_label_roots(root):
        mob.set_opacity(opacity)


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
            # ``family=False``: empty container groups must not zero stroke on
            # symbol Line submobjects (intro show_labels / normalize path).
            mob.set_stroke(width=0, opacity=0, family=False)


def label_text(
    string: str,
    *,
    font_size: float,
    color: object,
    font: str | None = None,
    role: str | None = None,
) -> Text:
    """Colored label with no visible glyph stroke; draws above wire segments."""
    kwargs: dict = {"font_size": font_size, "color": color}
    if font:
        kwargs["font"] = font
    label = Text(string, **kwargs)
    setattr(label, _ME_LABEL_COLOR_ATTR, ManimColor(color))
    if role is not None:
        setattr(label, _ME_LABEL_ROLE_ATTR, role)
    refresh_label_strokes(label)
    return label
