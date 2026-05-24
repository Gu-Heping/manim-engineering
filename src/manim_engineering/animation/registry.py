"""Minimal registry for animation primitives (extensible without a framework)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TypeVar, overload

from manim_engineering.animation.base import AnimationPrimitive

T = TypeVar("T", bound=AnimationPrimitive)

_REGISTRY: dict[str, type[AnimationPrimitive]] = {}


def _store(name: str, cls: type[T]) -> type[T]:
    existing = _REGISTRY.get(name)
    if existing is not None and existing is not cls:
        msg = (
            f"primitive already registered: {name!r} "
            f"(existing={existing.__name__}, new={cls.__name__})"
        )
        raise ValueError(msg)
    _REGISTRY[name] = cls
    return cls


@overload
def register_primitive(name: str, cls: type[T]) -> type[T]: ...


@overload
def register_primitive(name: str) -> Callable[[type[T]], type[T]]: ...


def register_primitive(
    name: str,
    cls: type[T] | None = None,
) -> type[T] | Callable[[type[T]], type[T]]:
    """Register a primitive class (decorator or direct call)."""
    if cls is not None:
        return _store(name, cls)

    def decorator(inner: type[T]) -> type[T]:
        return _store(name, inner)

    return decorator


def get_primitive(name: str) -> type[AnimationPrimitive]:
    """Look up a registered primitive class."""
    try:
        return _REGISTRY[name]
    except KeyError as exc:
        msg = f"unknown animation primitive: {name!r}"
        raise KeyError(msg) from exc


def registered_primitives() -> tuple[str, ...]:
    """Return registered primitive names in lexicographic order (stable for tests)."""
    return tuple(sorted(_REGISTRY))


def primitive_registry_view() -> Mapping[str, type[AnimationPrimitive]]:
    """Read-only snapshot of the registry (for diagnostics and tooling)."""
    return dict(_REGISTRY)
