"""Perceptual hashing helpers for visual golden tests."""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from PIL import Image

# Round before hashing so Manim Text/font metrics do not flip the digest.
GEOMETRY_HASH_DECIMALS = 4

DHASH_BITS = 64


def dhash_hex(image_path: Path, hash_size: int = 8) -> str:
    """Difference hash (dHash) as 16-char hex (64 bits)."""
    img = Image.open(image_path).convert("L").resize(
        (hash_size + 1, hash_size),
        Image.Resampling.LANCZOS,
    )
    pixels = list(img.get_flattened_data())
    bits: list[str] = []
    for row in range(hash_size):
        row_start = row * (hash_size + 1)
        for col in range(hash_size):
            left = pixels[row_start + col]
            right = pixels[row_start + col + 1]
            bits.append("1" if left > right else "0")
    return f"{int(''.join(bits), 2):016x}"


def stable_geometry_hash(mob) -> str:
    """SHA-256 of rounded point data for deterministic layout/render guards."""
    points = mob.get_all_points()
    rounded = np.round(np.asarray(points, dtype=np.float64), decimals=GEOMETRY_HASH_DECIMALS)
    return hashlib.sha256(rounded.tobytes()).hexdigest()


def layout_geometry_digest(layout) -> str:
    """Deterministic digest from placements, routed wires, and scene bbox (no waveform)."""
    parts: list[float] = []
    for placement in layout.placements:
        parts.extend(
            [
                placement.origin.x,
                placement.origin.y,
                placement.bounds.width,
                placement.bounds.height,
            ]
        )

    def _wire_sort_key(wire) -> tuple[float, ...]:
        if not wire.points:
            return ()
        first, last = wire.points[0], wire.points[-1]
        return (first.x, first.y, last.x, last.y, len(wire.points))

    for wire in sorted(layout.wires, key=_wire_sort_key):
        for pt in wire.points:
            parts.extend([pt.x, pt.y])
    parts.extend(
        [
            layout.scene_bbox.min_x,
            layout.scene_bbox.min_y,
            layout.scene_bbox.max_x,
            layout.scene_bbox.max_y,
            layout.occupancy_ratio,
        ]
    )
    rounded = np.round(np.asarray(parts, dtype=np.float64), decimals=GEOMETRY_HASH_DECIMALS)
    return hashlib.sha256(rounded.tobytes()).hexdigest()


def layout_waveform_geometry_digest(layout, bundle) -> str:
    """Deterministic digest from layout wires/placements and waveform polyline points."""
    from manim_engineering.waveform.layout import panel_below_layout, step_polyline

    parts: list[float] = []
    for placement in layout.placements:
        parts.extend(
            [
                placement.origin.x,
                placement.origin.y,
                placement.bounds.width,
                placement.bounds.height,
            ]
        )
    def _wire_sort_key(wire) -> tuple[float, ...]:
        if not wire.points:
            return ()
        first, last = wire.points[0], wire.points[-1]
        return (first.x, first.y, last.x, last.y, len(wire.points))

    for wire in sorted(layout.wires, key=_wire_sort_key):
        for pt in wire.points:
            parts.extend([pt.x, pt.y])
    spec = panel_below_layout(layout, trace_count=len(bundle.traces))
    parts.extend(
        [
            spec.origin.x,
            spec.origin.y,
            spec.width,
            spec.trace_height,
            spec.trace_gap,
            layout.scene_bbox.min_x,
            layout.scene_bbox.min_y,
            layout.scene_bbox.max_x,
            layout.scene_bbox.max_y,
        ]
    )
    for index, trace in enumerate(bundle.traces):
        for pt in step_polyline(trace, spec, index):
            parts.extend([pt.x, pt.y])
    rounded = np.round(np.asarray(parts, dtype=np.float64), decimals=GEOMETRY_HASH_DECIMALS)
    return hashlib.sha256(rounded.tobytes()).hexdigest()


def stable_geometry_hash_lines_only(mob) -> str:
    """Hash routed Line geometry only (excludes Manim Text label tessellation)."""
    try:
        from manim import Line
    except ImportError:
        return stable_geometry_hash(mob)

    chunks: list[np.ndarray] = []

    def walk(node) -> None:
        if isinstance(node, Line):
            pts = np.round(
                np.asarray(node.get_all_points(), dtype=np.float64),
                decimals=GEOMETRY_HASH_DECIMALS,
            )
            chunks.append(pts)
            return
        for sub in getattr(node, "submobjects", ()):
            walk(sub)

    walk(mob)
    if not chunks:
        return stable_geometry_hash(mob)
    combined = np.concatenate(chunks)
    return hashlib.sha256(combined.tobytes()).hexdigest()


def hamming_hex(a: str, b: str) -> int:
    """Hamming distance between two equal-length hex hashes."""
    if len(a) != len(b):
        raise ValueError(f"hash length mismatch: {len(a)} vs {len(b)}")
    return (int(a, 16) ^ int(b, 16)).bit_count()
