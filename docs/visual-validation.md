# Visual validation

Golden tests guard the **semantic → layout → render → frame** pipeline without changing semantics or animation APIs. They compare a rasterized last frame (perceptual hash) and optionally a point-geometry digest of the static circuit group.

## Architecture

```text
CircuitGraph + elements
        │
        ▼
LayoutEngine.solve / layout  →  LayoutResult (placements, wires)
        │
        ▼
ManimRenderer.render         →  VGroup (components, then wires)
        │
        ▼
AcceptanceScene (Manim)      →  last-frame PNG
        │
        ▼
tests/visual golden dHash    →  Hamming distance vs stored hash
```

**Z-order (examples with waveform):** add **components → wires → waveform panel** so routed nets stay under the timing panel. `MinimalRenderer.render_layout` already returns `VGroup(*placed, *wire_lines)`; scene code should not reorder wires above the panel.

**Invariants (governance Step 5):**

- `CircuitGraph.connect()` assigns **deterministic** `connection_id` values from sorted port ids (`conn-<a>--<b>`), not random UUIDs, so layout and goldens replay identically (`tests/core/test_graph_determinism.py`).
- `SignalFlow` must not mutate wire `Line` geometry—only overlays and highlights (`tests/animation/test_signal_flow_ownership.py`).
- Waveform panel and `step_polyline` bands stay at least `MIN_WAVEFORM_GAP` below routed wires (`tests/layout/test_scene_bbox.py`).

## Running locally

Requires Manim (same as examples):

```bash
pip install -e ".[dev]"
pytest tests/visual/ -v
```

Without Manim, visual tests are **skipped** (`requires_manim`), not failed.

## Updating goldens

After an intentional visual change (theme, layout, symbol geometry):

```bash
# Windows PowerShell
$env:UPDATE_VISUAL_GOLDEN = "1"
pytest tests/visual/ -v
# Linux/macOS
UPDATE_VISUAL_GOLDEN=1 pytest tests/visual/ -v
```

Commit updated files under `tests/visual/golden/`:

- `acceptance_three_layer.dhash.txt` — 64-bit dHash hex from last frame
- `acceptance_three_layer.geometry.txt` — SHA-256 of routed `Line` points only (`stable_geometry_hash_lines_only`, excludes label tessellation)
- `signal_chain_demo.dhash.txt` / `signal_chain_demo.geometry.txt` — resistor-chain demo
- `spi_byte_transfer.dhash.txt` — SPI demo last frame (Hamming ≤ 4)
- `spi_byte_transfer.geometry.txt` — layout + waveform panel digest (`layout_waveform_geometry_digest`, no raster)
- `uart_byte_transfer.dhash.txt` — UART demo last frame (Hamming ≤ 4)
- `uart_byte_transfer.geometry.txt` — UART layout + waveform digest (no raster)
- `rc_step_response.geometry.txt` — analog R1–C1 layout digest (`layout_geometry_digest`, no raster)

**Tolerance:** perceptual compare uses **Hamming distance ≤ 4** on the dHash (`tests/visual/conftest.py`).

## Geometry golden change discipline

When a change touches **waveform polyline construction** or **layout coordinates** that feed goldens, update **all** affected geometry files — not only the scene you were editing.

**Must run full visual suite** after edits to:

- `waveform/layout.py` — especially `step_polyline`, `panel_below_layout`, point deduplication
- `layout/engine.py` or `layout/routing.py` when wire/trace point lists change
- renderer symbol geometry that shifts pin anchors used by routing

```bash
# Windows PowerShell
$env:UPDATE_VISUAL_GOLDEN = "1"
pytest tests/visual/ -q
# Linux/macOS
UPDATE_VISUAL_GOLDEN=1 pytest tests/visual/ -q
```

Review **every** `tests/visual/golden/*.geometry.txt` diff in the PR, not just SPI or UART in isolation. A `step_polyline` dedupe fix can shift UART and `signal_chain_demo` digests even when the motivating bug was SPI-only.

## What goldens do *not* guarantee

- **dHash** compares a downscaled last frame; it does not assert pedagogical readability (label placement, wire-vs-symbol overlap, or interface box crowding).
- **Geometry digests** hash layout coordinates and waveform polyline points only — not Manim `Text` tessellation or pin labels.
- **Footprint clearance** is enforced separately in `tests/layout/test_footprint.py` via `assert_wires_avoid_footprints` (wire segment midpoints must not lie inside component interiors). Governance R1–C1 gap wiring remains in `tests/layout/test_governance_acceptance_wiring.py`.

Manual review PNGs: run `python scripts/export_visual_golden_previews.py` → `tests/visual/golden/previews/`.

Acceptance MP4s (same `ME_SUPPRESS_FADE=1`, medium quality except CMOS inverter at high quality):

```bash
python scripts/export_example_videos.py
```

Output: `media/videos/examples/*.mp4` (see `media/videos/examples/README.md`).

**Intro/dim contract:** waveform demos fade in symbol bodies while `label_text` pin
labels are hidden then revealed (`hide_labels` / `show_labels` in
`examples/_shared.py`). Beat-interval dim uses `stroke_only` label refresh so
labels dim with symbols. See [animation-timing.md](animation-timing.md) troubleshooting table.
HUD scenes must reserve subtitle band (`subtitle_band` or default HUD band in
`WaveformDemoScene`) to avoid intro/caption overlap with topology.

## CI

Workflow job `visual-golden` (Ubuntu, Python 3.12):

- Installs `manim==0.19.1` and pangocairo apt deps (same as main `test` job)
- Runs `pytest tests/visual/`
- **Blocking** (`continue-on-error` removed once goldens are stable on Ubuntu)

Main `pytest` on 3.11/3.12 does not require visual goldens to pass when Manim is absent; dev extra includes Manim for local/optional runs.

## Adding scenes

1. Add or reuse `build_fixture()` in an example module.
2. Render `AcceptanceScene`-style last frame with `tempconfig` (`quality=low_quality`, `save_last_frame=True`).
3. Store dHash under `tests/visual/golden/<scene>.dhash.txt`.
4. Mark tests with `@requires_manim` from `tests/visual/conftest.py`.

Prefer one acceptance scene per golden file; avoid mixing unrelated layouts in one PNG.
