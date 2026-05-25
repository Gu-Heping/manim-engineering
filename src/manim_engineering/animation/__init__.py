"""Animation layer: motion, highlights, propagation visuals.

Deferred stubs ``VoltagePulse`` and ``LogicTransition`` (from ``stubs``) are
exported for registry compatibility only — they raise ``NotImplementedError``
and must not be used in production teaching scenes. See ``docs/ROADMAP.md``.
"""

from manim_engineering.animation.analog_ramp import AnalogRamp
from manim_engineering.animation.base import AnimationPlan, AnimationPrimitive
from manim_engineering.animation.beat import play_propagation_beat
from manim_engineering.animation.focus import (
    dim_topology,
    normalize_topology_labels,
    restore_topology,
)
from manim_engineering.animation.layers import (
    HUD_Z_INDEX,
    PROPAGATION_Z_INDEX,
    PULSE_Z_INDEX,
    TIMING_Z_INDEX,
)
from manim_engineering.animation.pacing import (
    BEAT_CAPTION_HOLD,
    BEAT_DURATION,
    BEAT_GAP,
    CAPTION_CROSSFADE,
    INTRO_PAUSE,
    OUTRO_PAUSE,
    OVERLAY_FADE_OUT,
    SCENE_FADE_OUT,
    scene_final_fade_enabled,
    subtitle_text,
)
from manim_engineering.animation.propagation_sequence import (
    BeatSpec,
    PropagationSequence,
)
from manim_engineering.animation.purpose import AnimationPurpose
from manim_engineering.animation.registry import (
    get_primitive,
    primitive_registry_view,
    register_primitive,
    registered_primitives,
)
from manim_engineering.animation.scene import (
    SceneCamera,
    configure_topology_scene_camera,
    configure_waveform_scene_camera,
    resolve_scene_camera,
    resolve_topology_scene_camera,
)
from manim_engineering.animation.scene_template import play_topology_intro
from manim_engineering.animation.signal_flow import (
    DEFAULT_PROPAGATION_DURATION,
    SignalFlow,
)
from manim_engineering.animation.stubs import LogicTransition, VoltagePulse
from manim_engineering.animation.theme import (
    BACKGROUND_COLORS,
    DEFAULT_BACKGROUND,
    HIGHLIGHT_COLOR,
    MUTED_COLOR,
)
from manim_engineering.animation.waveform_reveal import WaveformRevealTracker
from manim_engineering.animation.waveform_sync import (
    DEFAULT_TIMING_DURATION,
    WaveformSync,
)

__all__ = [
    "AnalogRamp",
    "AnimationPlan",
    "AnimationPrimitive",
    "AnimationPurpose",
    "BACKGROUND_COLORS",
    "BEAT_CAPTION_HOLD",
    "BEAT_DURATION",
    "BEAT_GAP",
    "CAPTION_CROSSFADE",
    "BeatSpec",
    "DEFAULT_BACKGROUND",
    "DEFAULT_PROPAGATION_DURATION",
    "DEFAULT_TIMING_DURATION",
    "HIGHLIGHT_COLOR",
    "HUD_Z_INDEX",
    "INTRO_PAUSE",
    "LogicTransition",
    "MUTED_COLOR",
    "OUTRO_PAUSE",
    "OVERLAY_FADE_OUT",
    "PROPAGATION_Z_INDEX",
    "PULSE_Z_INDEX",
    "PropagationSequence",
    "SCENE_FADE_OUT",
    "SceneCamera",
    "SignalFlow",
    "TIMING_Z_INDEX",
    "VoltagePulse",
    "WaveformSync",
    "WaveformRevealTracker",
    "configure_topology_scene_camera",
    "configure_waveform_scene_camera",
    "dim_topology",
    "normalize_topology_labels",
    "get_primitive",
    "play_propagation_beat",
    "play_topology_intro",
    "primitive_registry_view",
    "register_primitive",
    "registered_primitives",
    "resolve_scene_camera",
    "resolve_topology_scene_camera",
    "restore_topology",
    "scene_final_fade_enabled",
    "subtitle_text",
]
