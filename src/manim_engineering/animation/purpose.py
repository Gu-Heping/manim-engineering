"""Animation purpose tags (required for every primitive)."""

from __future__ import annotations

from enum import Enum


class AnimationPurpose(str, Enum):
    """Why motion exists — decorative untagged motion is disallowed."""

    PROPAGATION = "propagation"
    TIMING = "timing"
    FOCUS = "focus"
    TRANSITION = "transition"
