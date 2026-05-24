"""Export analog scene preview PNGs for manual inspection.

Legacy visual golden PNG/dHash gates were removed. This script now provides
optional preview snapshots only (non-blocking).
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EXAMPLES = REPO / "examples"
OUT_DIR = REPO / "media" / "debug" / "previews"

# (output stem, example path relative to examples, scene class name)
PREVIEW_SCENES: tuple[tuple[str, str, str], ...] = (
    ("analog_01_rc_charge", "analog/01_rc_charge.py", "RCChargeScene"),
    ("analog_02_diode_rectifier", "analog/02_diode_rectifier.py", "HalfWaveRectifierScene"),
    ("analog_03_cmos_inverter", "analog/03_cmos_inverter.py", "CMOSInverterScene"),
    ("analog_04_npn_amplifier", "analog/04_npn_amplifier.py", "NPNAmplifierScene"),
    ("analog_05_opamp_inverting", "analog/05_opamp_inverting.py", "OpAmpInvertingScene"),
    ("analog_06_opamp_integrator", "analog/06_opamp_integrator.py", "OpAmpIntegratorScene"),
    ("analog_07_zener_regulator", "analog/07_zener_regulator.py", "ZenerRegulatorScene"),
    ("analog_08_rlc_transient", "analog/08_rlc_transient.py", "RLCTransientScene"),
)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _render_scene_last_frame(scene_cls: type, glob_pattern: str) -> Path:
    from manim import tempconfig

    with tempfile.TemporaryDirectory(prefix="me_preview_") as tmpdir:
        with tempconfig(
            {
                "quality": "low_quality",
                "disable_caching": True,
                "media_dir": tmpdir,
                "write_to_movie": False,
                "save_last_frame": True,
            }
        ):
            scene_cls().render()

        matches = sorted(Path(tmpdir).rglob(f"{glob_pattern}*.png"))
        if not matches:
            raise FileNotFoundError(f"no PNG matching {glob_pattern!r} under {tmpdir}")
        return matches[-1]


def main() -> None:
    os.environ.setdefault("ME_SUPPRESS_FADE", "1")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    from manim import __version__ as manim_version

    print(f"Manim CE {manim_version}")
    print(f"Writing previews to {OUT_DIR}\n")

    for stem, rel, cls_name in PREVIEW_SCENES:
        path = EXAMPLES / rel
        mod = _load_module(stem, path)
        scene_cls = getattr(mod, cls_name)
        png = _render_scene_last_frame(scene_cls, cls_name)
        dest = OUT_DIR / f"{stem}_last_frame.png"
        shutil.copy2(png, dest)
        print(f"  {dest.name}")


if __name__ == "__main__":
    main()
