"""Shared fixtures for visual golden tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _suppress_scene_final_fade(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set ``ME_SUPPRESS_FADE=1`` for the duration of every visual test.

    Scenes end with ``FadeOut(*self.mobjects)`` for cinematic CLI output, but
    visual golden tests capture ``save_last_frame``: without this gate the
    "last frame" would be a uniform background, making dHash regression
    detection useless.
    """
    monkeypatch.setenv("ME_SUPPRESS_FADE", "1")


try:
    import manim  # noqa: F401

    HAS_MANIM = True
except ImportError:
    HAS_MANIM = False

requires_manim = pytest.mark.skipif(
    not HAS_MANIM,
    reason="manim not installed (pip install -e '.[manim]')",
)

# Perceptual hash Hamming distance tolerance (governance report).
PHASH_HAMMING_TOLERANCE = 4


def _is_ci_environment() -> bool:
    """Detect common CI signal flags so accidental UPDATE_VISUAL_GOLDEN bypasses fail loudly."""
    for var in ("CI", "GITHUB_ACTIONS", "BUILDKITE", "TF_BUILD", "CIRCLECI", "GITLAB_CI"):
        value = os.environ.get(var)
        if value and value not in ("0", "false", "False"):
            return True
    return False


def assert_or_update_golden_text(
    golden_path: Path,
    actual: str,
    *,
    label: str,
) -> str:
    """Assert exact text equality, or record a new golden when env is set.

    Behaviour:
    - ``UPDATE_VISUAL_GOLDEN=1`` writes ``actual`` to disk and *skips* the test
      (caller never sees a stale comparison). CI environments refuse the
      env so a developer cannot accidentally rubber-stamp regressions.
    - Otherwise, the file is read and compared exactly to ``actual``.
    """
    if os.environ.get("UPDATE_VISUAL_GOLDEN"):
        if _is_ci_environment():
            raise RuntimeError(
                "UPDATE_VISUAL_GOLDEN is forbidden in CI; record goldens locally and commit."
            )
        golden_path.parent.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(actual + "\n", encoding="utf-8")
        pytest.skip(f"{label} golden updated via UPDATE_VISUAL_GOLDEN=1")

    if not golden_path.exists():
        pytest.skip(f"{label} golden not committed yet; set UPDATE_VISUAL_GOLDEN=1 once")
    expected = golden_path.read_text(encoding="utf-8").strip()
    assert actual == expected, (
        f"{label} regression: actual={actual} expected={expected}. "
        "Re-run with UPDATE_VISUAL_GOLDEN=1 after intentional visual change."
    )
    return expected
