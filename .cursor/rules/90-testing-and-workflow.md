# Testing and Workflow

Validation contracts and development process. Lowest precedence vs foundation and semantic rules.

## Testing Requirements

Meaningful features require:

- unit tests (construction, pins, bounds, semantics)
- integration tests where systems compose
- deterministic behavior checks
- minimal executable example

Bug fixes require regression test or reproducible failing example.

**Renderers**: deterministic geometry, label placement, routing consistency; snapshot tests when stable. Orientation or upright-label changes require ``tests/renderers/test_orientation_render.py`` and ``tests/renderers/test_vertical_label_placement.py`` (plus ``tests/layout/test_preset_label_api.py`` when preset label fields change).

**Animation**: timing stability, no silent mutation of unrelated systems.

**Architecture tests** (recommended): import direction matches layer model in `00-foundation.md`.

Snapshot updates: intentional only — verify visual, semantic, and architectural correctness before regenerating.

## Examples

Examples are architecture contracts. Each demonstrates **one** concept/workflow.

Structure: setup → semantic definition → rendering → animation → result.

Names: `basic_nmos.py`, `signal_propagation.py` — not `cool_demo.py`, `ultimate_animation.py`.

Progression: `basic/` → `intermediate/` → `advanced/`.

Examples must not bypass semantic layer, hardcode renderer logic, or use scene-specific hacks.

Broken examples = broken API.

## Development Workflow

**Task size**: one subsystem, abstraction, or feature group per change.

**Implementation order**: see `00-foundation.md` § Implementation Order.

**Diff discipline**: minimal diffs; no unrelated formatting, renames, or broad refactors in feature work.

**Reuse**: inspect existing APIs before new abstractions. Extension over duplication.

**Refactors**: only for simplification, deduplication, API stabilization — with explicit justification.

## AI-Assisted Development

Behave as incremental maintainer, not speculative framework inventor.

Before coding:

1. inspect existing abstractions  
2. identify layer and owner  
3. identify tests to extend  
4. minimize architectural impact  

Forbidden:

- rewrite architecture casually  
- abstractions without immediate use case  
- hidden global state  
- bypassing semantic APIs  
- giant god objects  
- unrelated file churn  

New abstractions require: immediate use case, layer justification, demonstrated reuse.

**Context**: prefer specific, scoped, testable tasks over ambiguous mega-prompts.

**Completion checklist**:

1. layer boundaries  
2. naming consistency  
3. reuse (no duplicates)  
4. deterministic behavior  
5. tests + minimal example  
6. renderer/component independence  

## PR and merge workflow

Delivery loop for AI-assisted changes. Stabilization vs feature tracks: [docs/ROADMAP.md](../../docs/ROADMAP.md) (**Stabilization** / **Feature backlog**).

### Branch naming and scope

| Kind | Prefix | Example |
|------|--------|---------|
| Docs / discipline | `docs/` | `docs/sync-roadmap-golden-discipline` |
| Core contracts | `core/` | `core/port-id-invariant` |
| Review / chore | `chore/` | `chore/stabilization-debt` |
| Awakening refactor | `refactor/awaken-*` | `refactor/awaken-spi-fsm` |

One PR, one theme. Prefer splitting **docs-only** from **behavior changes**.

### Pre-push gates (local)

Align with [CI](../../.github/workflows/ci.yml) before push:

```bash
ruff check src tests
pytest tests/ -q
```

When touching **layout**, **waveform** (`step_polyline`, `panel_below_layout`), **renderer geometry**, or pin anchors:

```bash
pytest tests/layout/test_scene_bbox.py -q
pytest tests/layout/test_geometry_overlap.py -q
pytest tests/layout/test_layout_stress.py -q
pytest tests/layout/test_analog_geometry_smoke.py -q
pytest tests/waveform/test_step_polyline_reveal.py -q
pytest tests/examples/test_smoke_entrypoints.py -q
```

Review any geometry digest/assertion updates in the touched tests. Do not rely on raster snapshots as merge gates.

### Open a PR

Use `gh pr create`. On Windows, pass the body with multiple `-m` flags (avoid shell heredoc).

**Body template** (required sections):

```markdown
## Summary
- …

## Test plan
- [ ] ruff check src tests
- [ ] pytest tests/ -q
- [ ] pytest tests/layout/test_scene_bbox.py -q
- [ ] pytest tests/layout/test_geometry_overlap.py -q
- [ ] pytest tests/layout/test_layout_stress.py -q
- [ ] pytest tests/layout/test_analog_geometry_smoke.py -q
- [ ] pytest tests/waveform/test_step_polyline_reveal.py -q
- [ ] pytest tests/examples/test_smoke_entrypoints.py -q
```

Write **why** in Summary; list commands actually run in Test plan.

### CI and review bots

Blocking jobs (must pass before merge):

| Job | What it runs |
|-----|----------------|
| `test (3.11)` | ruff + full pytest |
| `test (3.12)` | ruff + full pytest |
| `geometry-smoke` | layout/waveform geometry + retained smoke entrypoint subset |

**CodeRabbit** is informational. Triage as follows:

| Comment kind | Action |
|--------------|--------|
| **Actionable** (test leaks, correctness, would fail CI) | Fix and push |
| **Nitpick** (wording, formatting) | Fix if cheap; else defer with a PR comment |
| **Warning** (e.g. docstring coverage below threshold) | Not merge-blocking unless policy changes |
| **Architecture major** (e.g. stale ID cache vs live `Port.id`) | Follow semantic/core rules; document trade-off in PR |

**Project-specific regressions**:

- Tests touching [`animation/registry.py`](../../src/manim_engineering/animation/registry.py) must not leak into global `_REGISTRY` — use `monkeypatch` with a registry snapshot or explicit teardown.
- Changes to [`waveform/layout.py`](../../src/manim_engineering/waveform/layout.py) require full geometry regression review (not SPI-only).

### Fix loop

1. `gh pr checks <number>` — wait for CI.
2. Read CodeRabbit summary and **actionable** inline comments.
3. Scoped fix commit → push. Do **not** `git commit --amend` after the branch is on the remote unless the user explicitly requests it and the commit was not pushed.
4. Repeat until merge criteria are met.

### Merge criteria and method

**Merge when**:

- `test (3.11)`, `test (3.12)`, and `geometry-smoke` are green
- No unresolved **actionable** review (or risk accepted in the PR thread)
- User has asked to merge (agents do not merge on their own initiative)

**Default**: `gh pr merge --squash --delete-branch`

**Forbidden** without explicit user request:

- force-push `main` / `master`
- merge while CI is red
- weakening CI workflows or test gates to make a PR pass

## Visual validation (executable gates)

Geometry tests guard **semantic → layout → waveform geometry** without requiring raster dHash snapshots. Human overview: [docs/visual-validation.md](../../docs/visual-validation.md).

**Run locally** (same as CI):

```bash
pip install -e ".[dev]"
pytest tests/layout/test_scene_bbox.py -q
pytest tests/layout/test_geometry_overlap.py -q
pytest tests/layout/test_layout_stress.py -q
pytest tests/layout/test_analog_geometry_smoke.py -q
pytest tests/waveform/test_step_polyline_reveal.py -q
pytest tests/examples/test_smoke_entrypoints.py -q
```

These are deterministic geometry gates and should pass without visual snapshot regeneration.

**Manual visual inspection** (optional, non-blocking):

```bash
python scripts/export_example_videos.py
```

**Geometry discipline**: changes to `waveform/layout.py` (`step_polyline`, `panel_below_layout`), layout routing/engine wire point lists, or pin anchors must keep the geometry guard tests passing.

**Gates**:

- When touching **layout**, **waveform**, or **animation** paths, keep these passing before merge:
  - `tests/layout/test_scene_bbox.py` — `scene_bbox`, `MIN_WAVEFORM_GAP` point separation
  - `tests/layout/test_geometry_overlap.py` — wire vs waveform AABB band/segment guards
  - `tests/layout/test_layout_stress.py` — deterministic wire replay hash / occupancy band
- `tests/layout/test_analog_geometry_smoke.py` — analog fixture bbox/wire geometry smoke
  - `tests/waveform/test_step_polyline_reveal.py` — reveal-time polyline geometry contract
- `tests/examples/test_smoke_entrypoints.py` — analog fixture builders + retained smoke entrypoints
  - `tests/animation/test_signal_flow_ownership.py` — `SignalFlow` must not mutate wire geometry
  - `tests/core/test_graph_determinism.py` — deterministic `connection_id` / replay (graph iteration + Connection.id ordering)
  - `tests/semantic/test_signal_propagation.py::test_repeated_propagation_same_result` — `Signal.propagate` determinism

**Z-order / panel gap**: see `31-visual-geometry.md`.

## CI

Tests run in CI: imports, rendering stability, API compatibility, and geometry regression. Job `geometry-smoke` (Ubuntu, Python 3.12) runs geometry-only layout/waveform tests and is **blocking**.

## Performance

No premature optimization. Flag exponential layout, runaway animation cost, accidental quadratic patterns.
