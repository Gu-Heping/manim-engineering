"""Animation-layer visual tokens (3B1B teaching style).

Owned by ``animation/`` because these decisions are *scene-level*:
background colour, transient emphasis halo, secondary HUD copy. They are
the same across every renderer variant — switching minimal/ieee/iec must
not change the scene background or pulse halo.

Renderers MUST NOT read this module. Each renderer owns its own *semantic*
colours (POWER/GROUND/CLOCK/DATA, stroke widths, font sizes) under its own
``theme.py`` (e.g. ``renderers/minimal/theme.py``). The animation layer
consumes those via ``theme.color_for_signal_type`` etc., but the visual
contract for *the scene itself* lives here.
"""

from __future__ import annotations

# Warm dark blue — 3B1B convention; pure black (#000000) feels harsh on
# educational material and washes out coloured strokes.
DEFAULT_BACKGROUND = "#1e1e2e"

# Alternative dark backgrounds, ordered by preference. Kept as a tuple so
# callers can reason about "what's allowed" without re-importing each colour.
BACKGROUND_COLORS: tuple[str, ...] = ("#1e1e2e", "#111111", "#202124")

# Warm gold for transient emphasis: pulse outline, ``Indicate`` flashes.
# Picked from the 3B1B palette as a softer alternative to pure ``YELLOW``
# that does not clash with ``CLOCK_COLOR`` (also yellow in minimal renderer).
HIGHLIGHT_COLOR = "#FFCB6B"

# Subdued grey for secondary HUD copy (intro subtitle, helper labels).
# Matches Manim's ``GREY_B`` so it reads as "context, not focus".
MUTED_COLOR = "#BDBDBD"
