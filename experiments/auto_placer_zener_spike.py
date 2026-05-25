"""Isolated spike: compare grid-only vs preset layout for the zener regulator.

Not imported by ``LayoutEngine``. Run manually:

    python experiments/auto_placer_zener_spike.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from manim_engineering.layout import LayoutEngine  # noqa: E402
from manim_engineering.layout.presets.zener_regulator import JUNCTION  # noqa: E402


def main() -> None:
    spec = importlib.util.spec_from_file_location(
        "fixture", REPO / "examples/analog/07_zener_regulator.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    graph, elements, preset_layout = mod.build_zener_regulator_fixture()
    grid_layout = LayoutEngine().layout(graph, elements)

    preset_rs_b = preset_layout.pin_positions[elements["rs1"].get_pin("b").id]
    grid_rs_b = grid_layout.pin_positions[elements["rs1"].get_pin("b").id]
    delta_x = abs(grid_rs_b.x - preset_rs_b.x)
    delta_y = abs(grid_rs_b.y - preset_rs_b.y)

    print("Zener auto-placer spike (grid-only vs preset)")
    print(f"  preset junction target: ({JUNCTION.x}, {JUNCTION.y})")
    print(f"  preset rs.b:            ({preset_rs_b.x}, {preset_rs_b.y})")
    print(f"  grid   rs.b:            ({grid_rs_b.x}, {grid_rs_b.y})")
    print(f"  delta:                  dx={delta_x:.3f} dy={delta_y:.3f}")
    print(
        "  verdict: preset-first remains authoritative until delta < 0.2 on both axes"
    )


if __name__ == "__main__":
    main()
