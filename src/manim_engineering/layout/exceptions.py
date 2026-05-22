"""Layout-layer typed exceptions."""

from __future__ import annotations


class LayoutError(Exception):
    """Base exception for layout and routing failures."""


class UnknownElementError(LayoutError):
    """Raised when a graph node has no matching circuit element."""


class PlacementError(LayoutError):
    """Raised when placement constraints cannot be satisfied."""


class RoutingError(LayoutError):
    """Raised when an orthogonal route cannot be constructed."""
