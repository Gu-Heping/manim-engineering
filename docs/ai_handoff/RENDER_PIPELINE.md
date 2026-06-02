# RENDER_PIPELINE (for AI engineers)

## Static projection pipeline

1. `CircuitGraph` + `elements` + `LayoutResult` enter renderer.
2. `MinimalRenderer.render_layout(...)` emits:
   - placed component mobjects,
   - routed wire segments,
   - junction dots.
3. `ManimRenderer.render_topology(...)` wraps result as immutable topology projection.
4. `WaveformPanelRenderer.render_with_layout(...)` emits panel traces + axis.

## Renderer contract

- Renderer owns symbols, text placement, colors, stroke widths.
- Renderer must be deterministic for identical input.
- Renderer must not infer connectivity from geometry.
- Renderer must not animate or mutate semantic state.

## Geometry invariants you must not break

- `LayoutResult.scene_bbox` includes placed elements and routed wires.
- `MIN_WAVEFORM_GAP = 0.35` between lowest wire and waveform panel top.
- Scene draw order for waveform scenes: components -> wires -> panel.
- Wire paths remain immutable topology geometry during animations.

## Label system behavior

- Labels are renderer-owned (`label_text` + placement rules).
- Upright text survives orientation transforms via placement helpers.
- Per-element text overrides are layout metadata, not scene hacks.

## Waveform rendering specifics

- `idle_only=True` now means short idle stub by default (not full-width hold).
- `extend_to_panel` is explicit and opt-in per call path.
- Digital traces use step polyline logic; analog traces use smooth polyline.

## Visual correctness tests that gate pipeline changes

- `tests/layout/test_scene_bbox.py`
- `tests/layout/test_geometry_overlap.py`
- `tests/layout/test_layout_stress.py`
- `tests/waveform/test_step_polyline_reveal.py`
- `tests/layout/test_analog_geometry_smoke.py`

If a renderer/layout change bypasses these tests, treat it as incomplete.

