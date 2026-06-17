"""Renderer package import smoke test (no manim required)."""

from __future__ import annotations

import importlib
import sys

import pytest


def test_renderers_package_importable_without_manim() -> None:
    sys.modules.pop("manim_engineering.renderers", None)
    sys.modules.pop("manim_engineering.renderers.minimal", None)
    sys.modules.pop("manim_engineering.renderers.iec", None)

    module = importlib.import_module("manim_engineering.renderers")
    assert "MinimalRenderer" in module.__all__
    assert "ManimRenderer" in module.__all__
    assert "IECRenderer" in module.__all__
    assert "IECManimRenderer" in module.__all__
    assert "manim_engineering.renderers.minimal" not in sys.modules
    assert "manim_engineering.renderers.iec" not in sys.modules


def test_minimal_renderer_lazy_load_with_manim() -> None:
    pytest.importorskip("manim")
    from manim_engineering.renderers import ManimRenderer, MinimalRenderer

    assert MinimalRenderer.__name__ == "MinimalRenderer"
    assert ManimRenderer.__name__ == "ManimRenderer"


def test_iec_renderer_lazy_load_with_manim() -> None:
    pytest.importorskip("manim")
    from manim_engineering.renderers import IECManimRenderer, IECRenderer

    assert IECRenderer.__name__ == "IECRenderer"
    assert IECManimRenderer.__name__ == "IECManimRenderer"
