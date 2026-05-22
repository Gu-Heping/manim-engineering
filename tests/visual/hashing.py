"""Perceptual hashing helpers for visual golden tests."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

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


def hamming_hex(a: str, b: str) -> int:
    """Hamming distance between two equal-length hex hashes."""
    if len(a) != len(b):
        raise ValueError(f"hash length mismatch: {len(a)} vs {len(b)}")
    return (int(a, 16) ^ int(b, 16)).bit_count()
