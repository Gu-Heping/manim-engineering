"""Typed exceptions for the core graph model."""


class CoreError(Exception):
    """Base exception for core graph errors."""


class InvalidPortError(CoreError):
    """Raised when a port is missing, duplicated, or inconsistent."""


class InvalidConnectionError(CoreError):
    """Raised when a connection cannot be formed or torn down."""


class TopologyError(CoreError):
    """Raised when graph topology operations are invalid."""
