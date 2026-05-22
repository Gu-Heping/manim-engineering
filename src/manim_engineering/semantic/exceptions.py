"""Typed exceptions for the semantic layer."""

from manim_engineering.core.exceptions import (
    CoreError,
    InvalidPortError,
)

# Backward-compatible alias.
InvalidPinError = InvalidPortError


class SemanticError(CoreError):
    """Base exception for semantic-layer errors."""


class PropagationError(SemanticError):
    """Raised when signal propagation fails validation."""
