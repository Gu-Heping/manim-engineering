"""Animation layer: motion, highlights, propagation visuals."""

from manim_engineering.animation.base import AnimationPlan, AnimationPrimitive
from manim_engineering.animation.purpose import AnimationPurpose
from manim_engineering.animation.registry import (
    get_primitive,
    register_primitive,
    registered_primitives,
)
from manim_engineering.animation.signal_flow import (
    DEFAULT_PROPAGATION_DURATION,
    SignalFlow,
)
from manim_engineering.animation.stubs import LogicTransition, VoltagePulse
from manim_engineering.animation.waveform_sync import (
    DEFAULT_TIMING_DURATION,
    WaveformSync,
)

__all__ = [
    "AnimationPlan",
    "AnimationPrimitive",
    "AnimationPurpose",
    "DEFAULT_PROPAGATION_DURATION",
    "DEFAULT_TIMING_DURATION",
    "LogicTransition",
    "SignalFlow",
    "VoltagePulse",
    "WaveformSync",
    "get_primitive",
    "register_primitive",
    "registered_primitives",
]
