"""Typed exceptions for the component layer."""


class ComponentError(Exception):
    """Base exception for component-layer errors."""


class InvalidBoundsError(ComponentError):
    """Raised when component bounds are invalid."""
