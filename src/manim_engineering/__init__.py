"""Semantic engineering visualization framework."""

from __future__ import annotations

import importlib.util

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
    LabelPlacementMode,
    LayoutConfig,
    LayoutEngine,
    Point2D,
    RoutingIssueSeverity,
    TextPlacementOverride,
)
from manim_engineering.quickstart import (
    BuildParameterError,
    CircuitBuildResult,
    DiagramRenderResult,
    LayoutOutcome,
    build_circuit,
    export_circuit_preview,
    layout_circuit,
    render_circuit_diagram,
)

__version__ = "0.1.0"
_HAS_MANIM = importlib.util.find_spec("manim") is not None

__all__ = [
    "BuildParameterError",
    "Capacitor",
    "CircuitBuildResult",
    "CircuitGraph",
    "DiagramRenderResult",
    "Diode",
    "Ground",
    "Inductor",
    "InputDriver",
    "LabelPlacementMode",
    "LayoutConfig",
    "LayoutEngine",
    "LayoutOutcome",
    "NMOS",
    "NMOSDepletion",
    "NPN",
    "OpAmp",
    "PMOS",
    "PMOSDepletion",
    "PNP",
    "Point2D",
    "Resistor",
    "RoutingIssueSeverity",
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

if _HAS_MANIM:
    __all__.append("ManimRenderer")


def __getattr__(name: str) -> object:
    """Lazily expose optional renderer symbols without importing Manim eagerly."""

    if name == "ManimRenderer":
        if not _HAS_MANIM:
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
        from manim_engineering.renderers.minimal import ManimRenderer

        return ManimRenderer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
