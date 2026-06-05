# Layout Strategy

Human reference for when to use automatic grid placement, presets, or manual
overrides. Enforced rules: [`.cursor/rules/50-layout-routing.md`](../.cursor/rules/50-layout-routing.md).

## Pipeline

```text
CircuitGraph + elements
        │
        ├─ preset match? ──► layout/presets/* ──► placement_overrides (+ optional net waypoints)
        │
        └─ no preset ────► LayoutEngine.solve ──► place_on_grid_semantic
                                                    (VCC top / signal middle / GND bottom)
        │
        └─ always ───────► route_nets + visible stubs + deterministic detour pass
                           + deterministic spacing pass + routing diagnostics
                           + junction / crossing semantics
```

`LayoutEngine` now always returns a `routing_report` alongside wire geometry.
Use that report as the canonical post-routing diagnostic surface.

## When to use each mechanism

### Grid (`LayoutEngine.solve`)

Use for **simple left→right chains** where the teaching goal is signal flow,
not a fixed textbook schematic shape.

- Examples: `01_rc_charge`, `02_diode_rectifier`, `08_rlc_transient`
- ``place_on_grid_semantic`` separates VCC (top row), the signal chain (middle),
  and GND (bottom under the last signal element).
- Still deterministic; still overrideable per element if needed.

If the result is task-generated through the quickstart API, treat these warnings
as a signal that grid placement is the wrong tool for the job:

- ``layout.occupancy_above_target``
- ``layout.single_row_auto_grid``
- ``layout.branching_topology_using_auto_grid``

These warnings mean "render succeeded, but the layout likely needs preset or
manual help", not "the current geometry is acceptable".

Quickstart also surfaces routing-specific warnings when wiring still needs
attention:

- ``layout.routing_parallel_overlap``
- ``layout.routing_shared_segment``
- ``layout.routing_crossing_without_junction``
- ``layout.routing_wire_through_component``
- ``layout.routing_wire_near_unconnected_pin``

### Preset (`layout/presets/`)

Use when the scene needs a **canonical schematic shape** that grid placement
cannot produce reliably.

| Preset | Module | Scenes | Optional label/orient fields |
|--------|--------|--------|------------------------------|
| CMOS inverter stack | `presets/cmos_inverter.py` | 03 | ``orientation_overrides``, ``text_overrides``, ``label_mode_overrides`` |
| NPN common-emitter | `presets/npn_ce.py` | 04 | same |
| Op-amp inverting / integrator | `presets/opamp.py` | 05, 06 | same + ``net_waypoints`` / ``connection_waypoints`` |
| Zener shunt regulator | `presets/zener_regulator.py` | 07 | same (07 uses ``orientation_overrides`` for vertical Rs/Dz) |

Presets return ``overrides`` and optional maps above. Examples call
``layout_from_preset(LayoutEngine(), graph, elements, preset)`` — not duplicate
``LayoutEngine.layout`` kwargs inline.

### Component orientation

Symbols stay **canonical** in ``components/`` and ``renderers/``; rotation and
mirror are layout-time transforms only.

| API | Role |
|-----|------|
| ``ComponentOrientation(rotation=0/90/180/270, flip_x=…, flip_y=…)`` | Discrete transform per element |
| ``origin_for_pin_at(element, pin, target, orientation=…)`` | Pin-aligned placement origin |
| ``LayoutEngine.layout(..., orientation_overrides={id: orient})`` | Apply to grid and manual placements |
| ``ComponentPlacement.orientation`` | Consumed by ``MinimalRenderer._place_geometry_at`` |

Transform order (layout and renderer must match): **flip_x → flip_y → clockwise rotation**.

**Upright text:** ``label_text`` glyphs (component ids, ``+``/``-``, interface pin names)
are detached before geometry orientation and repositioned in world space without
flip/rotate. Default placement uses **screen-fixed semantic slots** relative to the
oriented footprint (e.g. component ids stay below OpAmp/BJT symbols on screen even
after ``flip_y``; horizontal passives stay above; MOSFET ids stay left).

**Label placement modes** (``LabelPlacementMode`` on ``ComponentPlacement``):

| Mode | Behavior |
|------|----------|
| ``AUTO`` (default) | Vertical two-terminal passives/diodes: score left/right label bands against neighbor footprints + wires; pick the freer side. |
| ``SLOT_ONLY`` | Skip auto side-picking; use type-based slots only (above/below/left). |

Priority (fixed): ``text_overrides[role]`` **>** ``AUTO`` smart side **>** type slot **>** oriented-local fallback.

Presets may pass ``text_overrides`` and ``label_mode_overrides`` into ``LayoutEngine.layout`` for manual pin positions or to disable auto on specific elements:

```python
TextPlacementOverride(role="component_label", world=Point2D(-0.35, 1.5))
```

Preset template:

```python
OP_ORIENTATION = ComponentOrientation(flip_y=True)
summation = Point2D(INPUT_COL_X, SUMMATION_Y)
op_origin = origin_for_pin_at(op, "in_n", summation, orientation=OP_ORIENTATION)

return MyPreset(
    overrides={op.element_id: op_origin, ...},
    orientation_overrides={op.element_id: OP_ORIENTATION},
    text_overrides={},  # optional manual label worlds
    label_mode_overrides={},  # optional SLOT_ONLY per id
)
```

Examples pass ``orientation_overrides=preset.orientation_overrides`` (and optional label maps) into
``LayoutEngine.layout``. Pin names keep semantic meaning (``in_p`` stays ``+``);
only screen positions change. See ``tests/layout/test_orientation.py`` and
``presets/opamp.py`` (scenes 05/06: ``flip_y`` puts ``in_n`` on top for
inverting topology).

### Manual override (escape hatch)

``placement_overrides`` pins a bottom-left origin for specific ``element_id`` values.
Use only while prototyping a new topology; **migrate to a preset** before the
example merges.

``orientation_overrides`` rotate or mirror symbols when the preset requires it.
See **Component orientation** above for the full contract.

## Routing report and spacing

Routing remains deterministic and explainable. The current layout path does not
run a global router; it augments the existing orthogonal wire plan with a small
post-pass and a diagnostics report.

### `routing_report`

Every ``LayoutResult`` now exposes:

- ``routing_report.issues``
- ``routing_report.highest_severity``
- ``routing_report.detoured_path_count``
- ``routing_report.spaced_track_count``
- ``routing_report.has_attention_items``

Current issue kinds:

| Kind | Meaning |
|------|---------|
| ``parallel_overlap`` | Two different wire paths still overlap along the same axis after spacing. |
| ``shared_segment`` | Two wire paths still share the same geometric segment after local shared-trunk splitting and spacing. |
| ``crossing_without_junction`` | Two wires cross in their interiors and the crossing point is not a declared electrical junction. |
| ``wire_through_component`` | A routed wire passes through the interior of another placed component footprint. |
| ``wire_near_unconnected_pin`` | A routed wire passes close enough to an unrelated pin anchor that the diagram may look falsely connected. |

Residual issues also carry a severity:

| Severity | Meaning |
|----------|---------|
| ``cosmetic`` | The route is still legible but visually crowded or redundant. |
| ``ambiguous`` | The route may miscommunicate electrical intent to a reader. |
| ``blocking`` | The remaining geometry violates a core layout contract and should be treated as must-fix. |

### Deterministic detour + spacing passes

After ``route_nets(...)``, layout first runs a small deterministic detour pass
for simple local hazards, then a conservative spacing pass for overlapping
tracks.

Current detour scope:

- single horizontal or vertical wire segments
- simple two-segment L-paths
- interior trunk segments on longer paths
- foreign component-body crossings and unrelated-pin ambiguity
- when several of those local hazards land on the same segment, layout may use
  one deterministic dogleg to clear the whole group
- for a two-segment L-path, layout may also flip to the alternate elbow when
  that clears hazards that neither individual leg rewrite can resolve
- for a longer orthogonal path, layout may also flip one adjacent corner pair
  locally when a hazard sits on an endpoint-adjacent leg that cannot be safely
  rewritten on its own

Current detour policy:

- local doglegs only; no global reroute or path search
- if a local detour resolves the hazard safely, the final ``routing_report`` no
  longer includes that issue
- if no safe local detour exists, layout keeps the original route and reports
  the residual problem
- ``routing_report.detoured_path_count`` counts how many wire paths were
  successfully rewritten by this pass

Current scope:

- only same-axis overlaps are considered
- single straight wires and multiple interior trunk segments can be rewritten
- simple two-segment L-paths may also rewrite an endpoint-adjacent segment while keeping the pin endpoint fixed
- spacing runs a small fixed number of deterministic passes until no new track conflicts appear
- endpoints stay attached to the same pins; the pass inserts short doglegs
- track assignment is stable and deterministic

Current non-goals:

- no A* or obstacle-aware reroute
- no global crossing minimization
- no automatic "best looking" bus router

Component obstacle avoidance is now **local-detour first**. Layout will try a
single rectangular dogleg around one blocking footprint for simple wire
segments, then report ``wire_through_component`` only if that local rewrite is
not safe or not sufficient.

Pin ambiguity is also **local-detour first**. Layout will try to shift a simple
segment onto a nearby track when it passes through the danger zone around an
unrelated pin anchor, then report ``wire_near_unconnected_pin`` only if no safe
local detour exists.

If spacing cannot safely rewrite a conflict, layout leaves the original wire in
place and records the problem in ``routing_report``.

## Junctions vs crossings

``junction_nodes`` are still the electrical source of truth.

- declared junctions render as solid dots
- non-junction crossings are reported in ``routing_report``
- the minimal renderer uses that report to add a small crossing mask so a
  visual crossing is distinguishable from an actual connection

This distinction is diagnostic-first: renderer behavior consumes layout
metadata instead of re-deriving connectivity from geometry.

For canonical ``net-*`` hub/spoke branches, benign same-net shared backbone and
same-net pin proximity are now treated as acceptable layout semantics rather
than warning-worthy routing defects. Residual issues on the warning surface are
intended to represent still-confusing geometry, not every reuse of a same-net
trunk.

## Global auto-placer (deferred)

Full netlist auto-placement (force-directed, simulated annealing, opaque
constraint solvers as the default path) is **not planned during stabilization**.

Rationale:

- Teaching schematics need **explainable, canonical shapes**.
- Most layout bugs (e.g. VCC/Rc overlap) are **preset/routing** issues, not missing global search.
- [Foundation priorities](../.cursor/rules/00-foundation.md) rank explainability above automation.

### Future spike criteria

Revisit auto-placement only when **two or more** hold:

- Catalog grows beyond ~15 scenes and >50% lack a preset class
- User-authored netlists arrive without maintainer-tuned overrides
- Preset maintenance cost exceeds a bounded solver investment

Spike scope (if ever run):

- Isolated script, **not** wired to ``LayoutEngine.solve`` by default
- Baseline fixture: zener regulator (`experiments/auto_placer_zener_spike.py`)
- Success: grid-only pin positions within ±0.2 of preset, plus footprint guards
- Failure: keep preset-first strategy (recorded in `tests/layout/test_auto_placer_deferred.py`)

## Tests

| Concern | Test module |
|---------|-------------|
| Preset geometry | `tests/layout/test_*_preset.py` |
| Semantic grid layers | `tests/layout/test_grid_semantic.py` |
| Deferred auto-placer baseline | `tests/layout/test_auto_placer_deferred.py` |
| All analog fixtures smoke | `tests/layout/test_analog_geometry_smoke.py` |
