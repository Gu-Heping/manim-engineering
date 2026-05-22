"""Typed exceptions for the semantic layer."""


class SemanticError(Exception):
    """Base exception for semantic-layer errors."""


class InvalidPinError(SemanticError):
    """Raised when a pin is missing, duplicated, or inconsistent."""


class InvalidConnectionError(SemanticError):
    """Raised when a connection cannot be formed or torn down."""


class PropagationError(SemanticError):
    """Raised when signal propagation fails validation."""


class TopologyError(SemanticError):
    """Raised when graph topology operations are invalid."""
