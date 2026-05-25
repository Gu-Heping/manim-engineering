"""Renderer-local symbol conventions (switchable without duplicating components)."""

from __future__ import annotations

from enum import Enum


class MosfetSymbolConvention(Enum):
    """MOSFET glyph variants; pin anchors stay fixed across conventions."""

    textbook_vertical = "textbook_vertical"
    ieee_simplified = "ieee_simplified"
    arrow_on_channel = "arrow_on_channel"
