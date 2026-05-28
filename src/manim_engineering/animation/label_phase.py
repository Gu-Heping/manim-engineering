"""Animation-owned label lifecycle policy for intro and beat phases."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from manim import Mobject

from manim_engineering.renderers.minimal.labels import label_category, label_role

LabelPhase = Literal["intro_annotation", "beat_setup", "beat_conclusion"]
TransitionProfile = Literal["default", "setup", "conclusion"]


@dataclass(frozen=True)
class LabelPhasePolicy:
    """Allowed phases per engine-owned label category."""

    power_phases: frozenset[LabelPhase] = frozenset(
        {"intro_annotation", "beat_setup", "beat_conclusion"}
    )
    io_phases: frozenset[LabelPhase] = frozenset(
        {"intro_annotation", "beat_setup", "beat_conclusion"}
    )
    device_phases: frozenset[LabelPhase] = frozenset({"beat_setup", "beat_conclusion"})
    net_phases: frozenset[LabelPhase] = frozenset({"beat_conclusion"})

    def phases_for(self, category: str) -> frozenset[LabelPhase]:
        if category == "power":
            return self.power_phases
        if category == "io":
            return self.io_phases
        if category == "net":
            return self.net_phases
        return self.device_phases


def resolve_label_category(label: Mobject) -> str:
    """Best-effort category resolution for renderer labels."""
    category = label_category(label)
    if category is not None:
        return category
    role = label_role(label) or ""
    if role == "net_label":
        return "net"
    if role.startswith("interface.pin."):
        return "io"
    if role == "component_label":
        return "device"
    return "device"


def label_allowed_in_phase(
    label: Mobject,
    phase: LabelPhase,
    policy: LabelPhasePolicy | None = None,
) -> bool:
    """Whether a label is eligible to appear in the given animation phase."""
    resolved = policy or LabelPhasePolicy()
    category = resolve_label_category(label)
    return phase in resolved.phases_for(category)


def phase_for_transition_profile(profile: TransitionProfile) -> LabelPhase | None:
    """Beat phase eligible for label focus under the given transition profile."""
    if profile == "setup":
        return "beat_setup"
    if profile == "conclusion":
        return "beat_conclusion"
    return None
