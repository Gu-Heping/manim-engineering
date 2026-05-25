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

**Global netlist auto-placement is deferred** during stabilization. Do not wire
force-directed or opaque solvers into ``LayoutEngine.solve``. Preset-first
layouts in ``layout/presets/`` remain authoritative for canonical teaching
shapes. See [docs/layout-strategy.md](../docs/layout-strategy.md) and
``experiments/auto_placer_zener_spike.py`` for the zener spike baseline.

`LayoutEngine.layout(graph, elements, *, placement_overrides=None)` accepts an
optional `Mapping[str, Point2D]` keyed by `element_id`. Elements present in the
map are pinned at the supplied bottom-left origin; absent elements still flow
through ``place_on_grid_semantic`` (VCC top, signal chain middle, GND bottom for
linear chains) or plain ``place_on_grid`` when no power symbols are present.
Unknown keys raise `UnknownElementError`. Use presets or overrides for
canonical topologies where the engine's left-to-right grid loses the
schematic shape (CMOS inverter vertical stack, analog stages with explicit
column structure). Avoid ad-hoc inline overrides in examples — prefer
``layout/presets/``.

## Placement strategy (grid vs preset vs override)

| Situation | Mechanism | Example |
|-----------|-----------|---------|
| Linear chain, no canonical shape | ``LayoutEngine.solve`` → ``place_on_grid_semantic`` | 01 RC, 02 rectifier, 08 RLC |
| Known teaching topology | ``layout/presets/*`` + ``placement_overrides`` | 03 CMOS, 04 NPN CE, 05/06 op-amp, 07 zener |
| Feedback / net hubs / GND detours | preset + ``net_waypoints`` / ``connection_waypoints`` | 05/06 op-amp |
| One-off tuning | ``placement_overrides`` only when no preset exists yet | migrate to preset before merge |

Full decision tree and deferred auto-placer criteria: [docs/layout-strategy.md](../docs/layout-strategy.md).

Preset examples MUST call ``layout_from_preset(engine, graph, elements, preset)``
(``layout/presets/_apply.py``) so ``orientation_overrides``, ``text_overrides``,
and ``label_mode_overrides`` are not dropped silently.

## Label placement (upright text)

Renderer-owned; layout supplies optional overrides on ``ComponentPlacement``.

Priority (fixed): ``text_overrides[role]`` **>** ``LabelPlacementMode.AUTO`` (vertical
band scoring) **>** type-based screen slot **>** oriented-local fallback.

- Manual label worlds belong on the **preset** (``text_overrides`` dict) or
  ``LayoutEngine.layout(..., text_overrides=…)`` — not hardcoded in example scenes.
- All preset dataclasses expose ``text_overrides`` and ``label_mode_overrides``
  (default empty). Use ``SLOT_ONLY`` per element when auto side-picking must be off.
- Human reference: [docs/layout-strategy.md](../docs/layout-strategy.md) § Label placement modes.

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
