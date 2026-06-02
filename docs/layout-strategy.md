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
        └─ always ───────► route_nets + visible stubs + junction dots
```

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
