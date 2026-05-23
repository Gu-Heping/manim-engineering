"""Golden visual regression for examples/protocol/uart_byte_transfer.UARTByteTransferDemo."""

from __future__ import annotations

import importlib.util
import os
import tempfile
from pathlib import Path

import pytest
from conftest import PHASH_HAMMING_TOLERANCE, requires_manim
from hashing import dhash_hex, hamming_hex

_GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
_GOLDEN_NAME = "uart_byte_transfer.dhash.txt"
_EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "protocol" / "uart_byte_transfer.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("uart_byte_transfer", _EXAMPLE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _render_last_frame_png() -> Path:
    mod = _load_module()
    pytest.importorskip("manim")
    from manim import tempconfig

    tmpdir = tempfile.mkdtemp(prefix="me_visual_")
    with tempconfig(
        {
            "quality": "low_quality",
            "disable_caching": True,
            "media_dir": tmpdir,
            "write_to_movie": False,
            "save_last_frame": True,
        }
    ):
        mod.UARTByteTransferDemo().render()

    matches = sorted(Path(tmpdir).rglob("UARTByteTransferDemo*.png"))
    if not matches:
        raise FileNotFoundError(f"no UARTByteTransferDemo PNG under {tmpdir}")
    return matches[-1]


@requires_manim
def test_uart_byte_transfer_last_frame_dhash() -> None:
    """Last frame of UARTByteTransferDemo matches golden dHash (Hamming <= tolerance)."""
    png = _render_last_frame_png()
    actual = dhash_hex(png)
    golden_path = _GOLDEN_DIR / _GOLDEN_NAME

    if os.environ.get("UPDATE_VISUAL_GOLDEN"):
        golden_path.write_text(actual + "\n", encoding="utf-8")
        pytest.skip("golden updated via UPDATE_VISUAL_GOLDEN=1")

    expected = golden_path.read_text(encoding="utf-8").strip()
    distance = hamming_hex(actual, expected)
    assert distance <= PHASH_HAMMING_TOLERANCE, (
        f"dHash Hamming {distance} > {PHASH_HAMMING_TOLERANCE}: "
        f"actual={actual} expected={expected}. "
        "Re-run with UPDATE_VISUAL_GOLDEN=1 after intentional visual change."
    )
