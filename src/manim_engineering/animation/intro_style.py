"""Scene-level intro animation tuning (topology reveal before beats)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntroStyle:
    """Controls geometry-aware topology intro (Line Create vs Polygon DrawBorderThenFill)."""

    border_fill_run_time: float = 0.5
    create_lag_ratio: float = 0.1
    use_border_fill: bool = True
