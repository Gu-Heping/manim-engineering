# Visual validation

Geometry-first validation guards the **semantic → layout → waveform geometry** pipeline
without relying on rasterized dHash snapshots.

## What is gated

Blocking checks focus on deterministic coordinates and spacing contracts:

- `tests/layout/test_scene_bbox.py` — `scene_bbox` covers routed wires and enforces
  `MIN_WAVEFORM_GAP` from waveform panel
- `tests/layout/test_geometry_overlap.py` — wire vs waveform segment AABB separation
- `tests/layout/test_layout_stress.py` — deterministic wire replay hash + occupancy
- `tests/waveform/test_step_polyline_reveal.py` — reveal-time waveform polyline geometry
- `tests/layout/test_analog_geometry_smoke.py` — analog fixture bbox/wire geometry smoke
  (scene `09_mos_four_types` has no cross-element wires — only placement/bbox checks)
- `tests/examples/test_smoke_entrypoints.py` — analog fixture builders + retained smoke entrypoints

These checks replace legacy dHash/PNG golden gates.

## Running locally

```bash
pip install -e ".[dev]"
pytest tests/layout/test_scene_bbox.py -q
pytest tests/layout/test_geometry_overlap.py -q
pytest tests/layout/test_layout_stress.py -q
pytest tests/layout/test_analog_geometry_smoke.py -q
pytest tests/waveform/test_step_polyline_reveal.py -q
pytest tests/examples/test_smoke_entrypoints.py -q
```

Run full regression when needed:

```bash
pytest tests/ -q
```

## Geometry change discipline

When touching geometry-producing paths:

- `src/manim_engineering/waveform/layout.py` (`step_polyline`, `panel_below_layout`)
- `src/manim_engineering/layout/engine.py` and `src/manim_engineering/layout/routing.py`
- renderer symbol geometry that shifts pin anchors

you must keep all geometry gate tests green and review changed assertions/digests in PRs.

## Manual visual inspection (optional)

Visual previews are not merge-blocking, but can be exported for sanity checks:

```bash
python scripts/export_example_videos.py
```

Output goes to `media/videos/examples/`.

## CI

Workflow gates:

- `test (3.11)` and `test (3.12)` — ruff + full pytest
- `geometry-smoke` — focused geometry/smoke regression suite

All three are blocking for merge.
