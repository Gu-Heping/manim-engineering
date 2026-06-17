"""Rendering layer: geometry, symbols, themes, labels."""

from __future__ import annotations

from typing import TYPE_CHECKING

__all__ = ["IECManimRenderer", "IECRenderer", "ManimRenderer", "MinimalRenderer"]

if TYPE_CHECKING:
    from manim_engineering.renderers.iec.renderer import IECManimRenderer as IECManimRenderer
    from manim_engineering.renderers.iec.renderer import IECRenderer as IECRenderer
    from manim_engineering.renderers.minimal.manim_renderer import ManimRenderer as ManimRenderer
    from manim_engineering.renderers.minimal.renderer import MinimalRenderer as MinimalRenderer


def __getattr__(name: str) -> type:
    if name == "IECManimRenderer":
        from manim_engineering.renderers.iec.renderer import IECManimRenderer

        return IECManimRenderer
    if name == "IECRenderer":
        from manim_engineering.renderers.iec.renderer import IECRenderer

        return IECRenderer
    if name == "ManimRenderer":
        from manim_engineering.renderers.minimal.manim_renderer import ManimRenderer

        return ManimRenderer
    if name == "MinimalRenderer":
        from manim_engineering.renderers.minimal.renderer import MinimalRenderer

        return MinimalRenderer
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
