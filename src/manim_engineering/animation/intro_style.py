"""Scene-level intro animation tuning (topology reveal before beats)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntroStyle:
    """Controls geometry-aware topology intro (Line Create vs Polygon DrawBorderThenFill)."""

    border_fill_run_time: float = 0.5
    create_lag_ratio: float = 0.1
    use_border_fill: bool = True
    per_stroke_run_time: float = 0.10
    min_stage_run_time: float = 0.5
    max_stage_run_time: float = 4.0
    stage_overhead: float = 0.15


def intro_run_time_budget(stroke_count: int, intro_style: IntroStyle | None = None) -> float:
    """Return a readable ``run_time`` for one intro stage from its stroke count."""
    style = intro_style or IntroStyle()
    if stroke_count <= 0:
        return style.min_stage_run_time
    raw = style.per_stroke_run_time * stroke_count + style.stage_overhead
    return min(style.max_stage_run_time, max(style.min_stage_run_time, raw))
