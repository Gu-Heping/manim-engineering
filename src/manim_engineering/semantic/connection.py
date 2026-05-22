"""Explicit connection between two pins."""

from __future__ import annotations

from dataclasses import dataclass

from manim_engineering.semantic.pin import Pin


@dataclass(frozen=True)
class Connection:
    """Undirected link between two pins in the topology."""

    id: str
    pin_a: Pin
    pin_b: Pin

    def involves(self, pin: Pin) -> bool:
        """Return True if ``pin`` is an endpoint of this connection."""
        return pin.id in (self.pin_a.id, self.pin_b.id)

    def other_pin(self, pin: Pin) -> Pin:
        """Return the peer pin for ``pin``."""
        if pin.id == self.pin_a.id:
            return self.pin_b
        if pin.id == self.pin_b.id:
            return self.pin_a
        msg = f"pin {pin.id} is not part of connection {self.id}"
        raise ValueError(msg)
