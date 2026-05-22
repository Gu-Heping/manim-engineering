# Visual Geometry

Executable layout and scene composition rules for waveform examples. Rendering draws geometry; this file owns numeric invariants.

## Scene bounding box

- `scene_bbox(placements, wires)` unions component footprints **and** all routed wire points.
- `LayoutResult.scene_bbox` must be populated by `LayoutEngine` (not `layout_bbox` alone).
- `panel_below_layout` places the waveform band using `scene_bbox.min_y` so wires extending below components stay in frame.

## Wire / waveform separation

- Minimum vertical gap between the lowest routed wire and the waveform panel top: **`MIN_WAVEFORM_GAP = 0.35`** (world units, `waveform/layout.py`).
- Tests: `tests/layout/test_scene_bbox.py` for the clock/data fixture.

## Z-order (waveform scenes)

Add to the scene in order: **components → wires → waveform panel**.

- `MinimalRenderer.render_layout` returns `VGroup(*placed, *wire_lines)`; scene code must not reorder wires above the panel.
- `SignalFlow` must not mutate wire `Line` geometry — only overlays and highlights.

## Golden guards

When changing layout, waveform panel placement, or minimal renderer wire/panel geometry:

- Keep `tests/layout/test_scene_bbox.py` passing.
- Update visual goldens per `90-testing-and-workflow.md` § Visual validation.
