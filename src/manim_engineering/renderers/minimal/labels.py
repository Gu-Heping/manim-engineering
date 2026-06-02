"""Shared Manim Text helpers for the minimal renderer."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Literal
from xml.etree.ElementTree import ParseError

import numpy as np
from manim import ManimColor, Mobject, Text

# Nets are pushed below component bodies; glyph paths must stay on top at pin rows.
WIRE_Z_INDEX = -1
LABEL_Z_INDEX = 1

_ME_LABEL_COLOR_ATTR = "_me_label_color"
_ME_LABEL_ROLE_ATTR = "_me_label_role"
_ME_LABEL_CATEGORY_ATTR = "_me_label_category"
_ME_LABEL_VISIBLE_ATTR = "_me_label_visible"
_ME_LABEL_DISPLAY_OPACITY_ATTR = "_me_label_display_opacity"

LabelRefreshMode = Literal["full", "stroke_only"]


def _purge_empty_text_svgs() -> None:
    texts_dir = Path.cwd() / "media" / "texts"
    if not texts_dir.is_dir():
        return
    for path in texts_dir.glob("*.svg"):
        try:
            if path.stat().st_size == 0:
                path.unlink()
        except OSError:
            continue


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


def label_category(mob: Mobject) -> str | None:
    """Engine-owned label category used by animation phase policy."""
    category = getattr(mob, _ME_LABEL_CATEGORY_ATTR, None)
    return category if isinstance(category, str) else None


def label_visible(mob: Mobject) -> bool:
    """Engine-owned visibility state for label roots."""
    visible = getattr(mob, _ME_LABEL_VISIBLE_ATTR, None)
    if isinstance(visible, bool):
        return visible
    return float(mob.get_opacity()) > 0.01


def _label_display_opacity(mob: Mobject) -> float:
    stored = getattr(mob, _ME_LABEL_DISPLAY_OPACITY_ATTR, None)
    if isinstance(stored, (int, float)):
        return float(stored)
    return 1.0


def _set_label_state(
    mob: Mobject,
    *,
    visible: bool | None = None,
    display_opacity: float | None = None,
) -> None:
    if visible is not None:
        setattr(mob, _ME_LABEL_VISIBLE_ATTR, bool(visible))
    if display_opacity is not None:
        setattr(mob, _ME_LABEL_DISPLAY_OPACITY_ATTR, float(display_opacity))


def _effective_label_opacity(mob: Mobject) -> float:
    return _label_display_opacity(mob) if label_visible(mob) else 0.0


def label_target_opacity(mob: Mobject) -> float:
    """Visible-state-aware opacity animation target for one label root."""
    return _effective_label_opacity(mob)


def set_label_visible(mob: Mobject, visible: bool) -> None:
    """Update the engine visibility state for one label root."""
    _set_label_state(mob, visible=visible)


def _role_filter(roles: str | Iterable[str] | None) -> frozenset[str] | None:
    if roles is None:
        return None
    if isinstance(roles, str):
        return frozenset((roles,))
    return frozenset(role for role in roles if isinstance(role, str))


def iter_label_roots(
    root: Mobject,
    *,
    roles: str | Iterable[str] | None = None,
) -> tuple[Mobject, ...]:
    """Every ``label_text`` root under ``root`` (deduplicated by identity)."""
    role_filter = _role_filter(roles)
    seen: set[int] = set()
    roots: list[Mobject] = []
    for mob in root.get_family():
        if not is_label_root(mob):
            continue
        role = label_role(mob)
        if role_filter is not None and role not in role_filter:
            continue
        sid = id(mob)
        if sid in seen:
            continue
        seen.add(sid)
        roots.append(mob)
    return tuple(roots)


def detach_label_roots(
    root: Mobject,
    *,
    roles: str | Iterable[str] | None = None,
) -> tuple[Mobject, ...]:
    """Remove label roots from ``root`` and return them in stable family order."""
    role_filter = _role_filter(roles)
    removed: list[Mobject] = []

    def _clear_container_points(ancestors: tuple[Mobject, ...]) -> None:
        for ancestor in ancestors:
            if ancestor.__class__.__name__ not in {"Group", "VGroup"}:
                continue
            clear_points = getattr(ancestor, "clear_points", None)
            if callable(clear_points):
                clear_points()

    def _walk(parent: Mobject, ancestors: tuple[Mobject, ...]) -> None:
        for mob in tuple(getattr(parent, "submobjects", ())):
            if is_label_root(mob):
                role = label_role(mob)
                if role_filter is None or role in role_filter:
                    parent.remove(mob)
                    removed.append(mob)
                    _clear_container_points((*ancestors, parent))
                    continue
            _walk(mob, (*ancestors, parent))

    _walk(root, ())
    return tuple(removed)


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
        mob.set_fill(opacity=0.0, family=False)


def restore_stroke_reveal(mobjects: tuple[Mobject, ...]) -> None:
    """Persist visibility after intro ``Create`` / ``DrawBorderThenFill``."""
    for mob in mobjects:
        name = mob.__class__.__name__
        if name == "Line":
            mob.set_stroke(opacity=1.0, family=False)
            mob.set_fill(opacity=0.0, family=False)
        elif name in ("Polygon", "Dot"):
            mob.set_stroke(opacity=1.0, family=False)
            mob.set_fill(opacity=1.0, family=False)
        elif mob.get_stroke_width() > 0:
            mob.set_stroke(opacity=1.0, family=False)
        elif (fill_opacity := mob.get_fill_opacity()) is not None and fill_opacity > 0.0:
            mob.set_fill(opacity=1.0, family=False)


def restore_waveform_strokes(lines: tuple[Mobject, ...]) -> None:
    """Persist trace ``Line`` visibility after beat/baseline ``Create``."""
    from manim_engineering.renderers.minimal import theme

    for mob in lines:
        if mob.__class__.__name__ != "Line":
            continue
        mob.set_stroke(
            width=theme.WAVEFORM_STROKE_WIDTH,
            opacity=1.0,
            family=False,
        )
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


def apply_label_opacity(
    root: Mobject,
    opacity: float,
    *,
    roles: str | Iterable[str] | None = None,
) -> None:
    """Dim or restore label roots without touching symbol ``Line`` geometry."""
    for mob in iter_label_roots(root, roles=roles):
        _set_label_state(mob, display_opacity=opacity)
        mob.set_opacity(_effective_label_opacity(mob))


def hide_labels(root: Mobject, *, roles: str | Iterable[str] | None = None) -> None:
    """Set label roots to invisible (intro: fade bodies without animating glyphs)."""
    for mob in iter_label_roots(root, roles=roles):
        _set_label_state(mob, visible=False)
        mob.set_opacity(0.0)


def show_labels(root: Mobject, *, roles: str | Iterable[str] | None = None) -> None:
    """Reveal label roots and restore fill/stroke after a body-only fade."""
    for mob in iter_label_roots(root, roles=roles):
        _set_label_state(mob, visible=True)
        mob.set_opacity(_effective_label_opacity(mob))
    refresh_label_strokes(root, mode="full", roles=roles)


def _apply_label_glyph_style(
    mob: Mobject,
    color: ManimColor,
    *,
    stroke_only: bool = False,
    fill_opacity: float | None = None,
) -> None:
    """Restore one Text glyph (or container) after parent opacity animations."""
    transparent = np.array([*color.to_rgb(), 0.0], dtype=float)
    if not stroke_only:
        mob.set_fill(color, opacity=1.0 if fill_opacity is None else fill_opacity)
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


def refresh_label_strokes(
    root: Mobject,
    *,
    mode: LabelRefreshMode = "full",
    roles: str | Iterable[str] | None = None,
) -> None:
    """Re-apply label styling after ``set_opacity`` / ``FadeIn`` on a parent.

    ``full`` restores fill and zeroes stroke (after restore or intro reveal).
    ``stroke_only`` zeroes corrupted glyph strokes without forcing fill opacity
    to 1.0 while labels remain dimmed.
    ``roles`` limits the refresh to selected semantic label groups.
    """
    stroke_only = mode == "stroke_only"
    roots = iter_label_roots(root, roles=roles)
    touched: set[int] = set()
    for mob in roots:
        color = _label_color(mob)
        if color is None:
            continue
        fill_opacity = _effective_label_opacity(mob)
        for sub in mob.get_family():
            sid = id(sub)
            if sid in touched:
                continue
            touched.add(sid)
            _apply_label_glyph_style(
                sub,
                color,
                stroke_only=stroke_only,
                fill_opacity=fill_opacity,
            )

    if stroke_only:
        return

    for mob in roots:
        for sub in mob.get_family():
            if id(sub) in touched:
                continue
            if len(sub.points) == 0:
                # ``family=False``: empty container groups must not zero stroke on
                # symbol Line submobjects (intro show_labels / normalize path).
                sub.set_stroke(width=0, opacity=0, family=False)


def label_text(
    string: str,
    *,
    font_size: float,
    color: object,
    font: str | None = None,
    role: str | None = None,
    category: str | None = None,
) -> Text:
    """Colored label with no visible glyph stroke; draws above wire segments."""
    kwargs: dict = {"font_size": font_size, "color": color}
    if font:
        kwargs["font"] = font
    try:
        label = Text(string, **kwargs)
    except (ParseError, FileNotFoundError, PermissionError):
        _purge_empty_text_svgs()
        label = Text(string, use_svg_cache=False, **kwargs)
    setattr(label, _ME_LABEL_COLOR_ATTR, ManimColor(color))
    if role is not None:
        setattr(label, _ME_LABEL_ROLE_ATTR, role)
    if category is not None:
        setattr(label, _ME_LABEL_CATEGORY_ATTR, category)
    _set_label_state(label, visible=True, display_opacity=1.0)
    refresh_label_strokes(label)
    return label
