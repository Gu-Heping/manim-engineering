"""Export standalone NPN/PNP BJT symbol PNGs for documentation."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "media" / "debug" / "previews"


def _render_last_frame(scene_cls: type, glob_pattern: str, dest: Path) -> None:
    from manim import tempconfig

    with tempfile.TemporaryDirectory(prefix="me_bjt_") as tmpdir:
        with tempconfig(
            {
                "quality": "low_quality",
                "disable_caching": True,
                "media_dir": tmpdir,
                "write_to_movie": False,
                "save_last_frame": True,
                "background_color": "#1a1a2e",
            }
        ):
            scene_cls().render()
        matches = sorted(Path(tmpdir).rglob(f"{glob_pattern}*.png"))
        if not matches:
            raise FileNotFoundError(f"no PNG matching {glob_pattern!r} under {tmpdir}")
        shutil.copy2(matches[-1], dest)


def main() -> None:
    from manim import Scene

    from manim_engineering.components import NPN, PNP
    from manim_engineering.renderers.minimal import MinimalRenderer

    class NpnOnlyScene(Scene):
        def construct(self) -> None:
            self.add(MinimalRenderer().render(NPN("q1", label="NPN")))

    class PnpOnlyScene(Scene):
        def construct(self) -> None:
            self.add(MinimalRenderer().render(PNP("q2", label="PNP")))

    class BjtPairScene(Scene):
        def construct(self) -> None:
            npn = MinimalRenderer().render(NPN("q1", label="NPN"))
            pnp = MinimalRenderer().render(PNP("q2", label="PNP"))
            npn.shift([-1.1, 0.0, 0.0])
            pnp.shift([1.1, 0.0, 0.0])
            self.add(npn, pnp)

    os.environ.setdefault("ME_SUPPRESS_FADE", "1")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    exports = (
        ("bjt_npn_standalone", NpnOnlyScene, "NpnOnlyScene"),
        ("bjt_pnp_standalone", PnpOnlyScene, "PnpOnlyScene"),
        ("bjt_npn_pnp_pair", BjtPairScene, "BjtPairScene"),
    )
    for stem, scene_cls, pattern in exports:
        dest = OUT_DIR / f"{stem}.png"
        _render_last_frame(scene_cls, pattern, dest)
        print(dest)


if __name__ == "__main__":
    main()
