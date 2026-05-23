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

Traces align with related signals, buses, and protocol events. Scene bbox, panel gap, and z-order: see `31-visual-geometry.md`.

## Auto-layout

Predictable, explainable, overrideable — no magical placement.

`LayoutEngine.layout(graph, elements, *, placement_overrides=None)` accepts an
optional `Mapping[str, Point2D]` keyed by `element_id`. Elements present in the
map are pinned at the supplied bottom-left origin; absent elements still flow
through `place_on_grid`. Unknown keys raise `UnknownElementError`. Use for
canonical topologies where the engine's left-to-right grid loses the
schematic shape (CMOS inverter vertical stack, analog stages with explicit
column structure). Avoid for routine scenes — manual origins are brittle.

## Wire vs footprint

Routed segments must not pass through the **interior** of unrelated component
footprints (endpoints on pin anchors at the border are OK). Use
`assert_wires_avoid_footprints(layout)` from `layout.footprint` in layout
tests; see `tests/layout/test_footprint.py`.

When merged hints include both `horizontal` and `vertical` with `up`/`down`
(e.g. resistor → NMOS drain), `route_orthogonal` prefers **vertical-first**
so bends do not cut through the channel at gate height.

## Determinism

No random placement, unstable routing order, or geometry jitter.
