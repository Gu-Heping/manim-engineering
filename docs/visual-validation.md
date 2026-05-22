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

**Invariant:** `SignalFlow` must not mutate wire `Line` geometry—only overlays and highlights.

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
- `acceptance_three_layer.geometry.txt` — SHA-256 of `ManimRenderer` point data (optional guard)

**Tolerance:** perceptual compare uses **Hamming distance ≤ 4** on the dHash (`tests/visual/conftest.py`).

## CI

Workflow job `visual-golden` (Ubuntu, Python 3.12):

- Installs `manim==0.19.1` and pangocairo apt deps (same as main `test` job)
- Runs `pytest tests/visual/`
- Initially `continue-on-error: true` until goldens are stable across runners; then flip to blocking

Main `pytest` on 3.11/3.12 does not require visual goldens to pass when Manim is absent; dev extra includes Manim for local/optional runs.

## Adding scenes

1. Add or reuse `build_fixture()` in an example module.
2. Render `AcceptanceScene`-style last frame with `tempconfig` (`quality=low_quality`, `save_last_frame=True`).
3. Store dHash under `tests/visual/golden/<scene>.dhash.txt`.
4. Mark tests with `@requires_manim` from `tests/visual/conftest.py`.

Prefer one acceptance scene per golden file; avoid mixing unrelated layouts in one PNG.
