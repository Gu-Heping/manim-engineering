"""Renderer package import smoke test (no manim required)."""

from __future__ import annotations

import importlib

import pytest


def test_renderers_package_importable_without_manim() -> None:
    module = importlib.import_module("manim_engineering.renderers")
    assert "MinimalRenderer" in module.__all__


def test_minimal_renderer_lazy_load_with_manim() -> None:
    pytest.importorskip("manim")
    from manim_engineering.renderers import MinimalRenderer

    assert MinimalRenderer.__name__ == "MinimalRenderer"
