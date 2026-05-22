# Layout and Routing

Spatial organization in `layout/` reinforces engineering meaning. Layout does not define topology semantics.

## Priorities

1. readability
2. topology clarity
3. signal flow clarity
4. subsystem grouping
5. routing cleanliness

Clarity over compactness.

## Placement

- Grid alignment, orthogonal paths, stable spacing
- Preferred flow: left→right, top→bottom
- Scene occupancy target: **60%–75%** of frame (whitespace aids comprehension)
- Minimize wire crossings via rerouting, bus grouping, hierarchy separation

## Components & Layout

Components expose: anchor points, bounds, routing hints, preferred connection directions.

Layout MUST use hints — not raw geometry inspection.

## Routing Ownership

Centralized in layout systems. Components provide hints only; they do not route global topology.

## Subsystem Grouping

Spatially group: power, timing, protocol interfaces, analog stages, digital stages.

## Buses

Grouped layout: shared direction, synchronization visible, hierarchy clear.

## Waveform Alignment

Traces align with related signals, buses, and protocol events.

## Scene geometry (executable)

- `scene_bbox(placements, wires)` unions component footprints **and** all routed wire points; `LayoutResult.scene_bbox` must be populated by `LayoutEngine`.
- `panel_below_layout` places the waveform band using `scene_bbox.min_y`, not `layout_bbox` alone (wires may extend below components).
- Minimum vertical gap between the lowest routed wire and the waveform panel top: **`MIN_WAVEFORM_GAP = 0.35`** (world units). Tests assert this for the clock/data fixture.

## Auto-layout

Predictable, explainable, overrideable — no magical placement.

## Determinism

No random placement, unstable routing order, or geometry jitter.
