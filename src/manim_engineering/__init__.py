"""Semantic engineering visualization framework."""

from __future__ import annotations

from typing import TYPE_CHECKING

from manim_engineering.components import (
    NMOS,
    NPN,
    PMOS,
    PNP,
    VCC,
    Capacitor,
    Diode,
    Ground,
    Inductor,
    InputDriver,
    NMOSDepletion,
    OpAmp,
    PMOSDepletion,
    Resistor,
    SPIMaster,
    SPISlave,
    UARTPort,
    ZenerDiode,
)
from manim_engineering.core import CircuitGraph, SignalType
from manim_engineering.layout import (
    LayoutConfig,
    LayoutEngine,
    Point2D,
    TextPlacementOverride,
)
from manim_engineering.quickstart import (
    CircuitBuildResult,
    DiagramRenderResult,
    LayoutOutcome,
    build_circuit,
    export_circuit_preview,
    layout_circuit,
    render_circuit_diagram,
)

if TYPE_CHECKING:
    from manim_engineering.renderers.minimal import ManimRenderer

__version__ = "0.1.0"

__all__ = [
    "Capacitor",
    "CircuitBuildResult",
    "CircuitGraph",
    "DiagramRenderResult",
    "Diode",
    "Ground",
    "Inductor",
    "InputDriver",
    "LayoutConfig",
    "LayoutEngine",
    "LayoutOutcome",
    "ManimRenderer",
    "NMOS",
    "NMOSDepletion",
    "NPN",
    "OpAmp",
    "PMOS",
    "PMOSDepletion",
    "PNP",
    "Point2D",
    "Resistor",
    "SignalType",
    "SPIMaster",
    "SPISlave",
    "TextPlacementOverride",
    "UARTPort",
    "VCC",
    "ZenerDiode",
    "build_circuit",
    "export_circuit_preview",
    "layout_circuit",
    "render_circuit_diagram",
]


def __getattr__(name: str) -> object:
    """Lazily expose optional renderer symbols without importing Manim eagerly."""

    if name == "ManimRenderer":
        from manim_engineering.renderers.minimal import ManimRenderer

        return ManimRenderer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
