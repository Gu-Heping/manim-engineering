"""Rendering layer: geometry, symbols, themes, labels."""

from __future__ import annotations

from typing import TYPE_CHECKING

__all__ = ["MinimalRenderer"]

if TYPE_CHECKING:
    from manim_engineering.renderers.minimal.renderer import MinimalRenderer as MinimalRenderer


def __getattr__(name: str) -> type:
    if name == "MinimalRenderer":
        from manim_engineering.renderers.minimal.renderer import MinimalRenderer

        return MinimalRenderer
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
