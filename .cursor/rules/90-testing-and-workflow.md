# Testing and Workflow

Validation contracts and development process. Lowest precedence vs foundation and semantic rules.

## Testing Requirements

Meaningful features require:

- unit tests (construction, pins, bounds, semantics)
- integration tests where systems compose
- deterministic behavior checks
- minimal executable example

Bug fixes require regression test or reproducible failing example.

**Renderers**: deterministic geometry, label placement, routing consistency; snapshot tests when stable.

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

## Visual validation (executable gates)

Golden tests guard **semantic → layout → render → frame** without changing semantics or animation APIs. Human overview: [docs/visual-validation.md](../../docs/visual-validation.md).

**Run locally** (requires Manim, same pin as CI):

```bash
pip install -e ".[dev]"
pytest tests/visual/ -v
```

Without Manim, visual tests are **skipped** (`requires_manim`), not failed.

**Update goldens** after intentional visual change:

```bash
# Windows PowerShell
$env:UPDATE_VISUAL_GOLDEN = "1"
pytest tests/visual/ -v
# Linux/macOS
UPDATE_VISUAL_GOLDEN=1 pytest tests/visual/ -v
```

Commit updated files under `tests/visual/golden/` (`<scene>.dhash.txt`, optional `<scene>.geometry.txt`).

**Gates**:

- Perceptual compare: dHash Hamming distance **≤ 4** (`PHASH_HAMMING_TOLERANCE` in `tests/visual/conftest.py`).
- When touching **layout**, **waveform**, or **animation** paths, keep these passing before merge:
  - `tests/layout/test_scene_bbox.py` — `scene_bbox`, `MIN_WAVEFORM_GAP` point separation
  - `tests/layout/test_geometry_overlap.py` — wire vs waveform AABB band/segment guards
  - `tests/animation/test_signal_flow_ownership.py` — `SignalFlow` must not mutate wire geometry
  - `tests/core/test_graph_determinism.py` — deterministic `connection_id` / replay (graph iteration + Connection.id ordering)
  - `tests/semantic/test_signal_propagation.py::test_repeated_propagation_same_result` — `Signal.propagate` determinism
  - `tests/visual/` — dHash and geometry goldens (`@requires_manim` for raster tests)
- Canonical scenes: `acceptance_three_layer`, `clock_data_waveform`, `signal_chain_demo`, `spi_byte_transfer` (one acceptance scene per golden PNG).

**Z-order / panel gap**: see `31-visual-geometry.md`.

## CI

Tests run in CI: imports, rendering stability, API compatibility, basic examples. Job `visual-golden` (Ubuntu, Python 3.12, `manim==0.19.1`) runs `pytest tests/visual/` and is **blocking**. Main matrix `pytest` skips visual tests when Manim is absent. Broken CI is blocking.

## Performance

No premature optimization. Flag exponential layout, runaway animation cost, accidental quadratic patterns.
