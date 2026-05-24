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
pytest tests/ -q --ignore=tests/visual
```

When touching **layout**, **waveform** (`step_polyline`, `panel_below_layout`), **renderer geometry**, or pin anchors:

```bash
pytest tests/visual/ -v
# intentional visual change:
# UPDATE_VISUAL_GOLDEN=1 pytest tests/visual/ -v
```

Review **all** `tests/visual/golden/*.geometry.txt` diffs — see [geometry golden discipline](#visual-validation-executable-gates) and [docs/visual-validation.md](../../docs/visual-validation.md#geometry-golden-change-discipline).

### Open a PR

Use `gh pr create`. On Windows, pass the body with multiple `-m` flags (avoid shell heredoc).

**Body template** (required sections):

```markdown
## Summary
- …

## Test plan
- [ ] ruff check src tests
- [ ] pytest tests/ -q --ignore=tests/visual
- [ ] pytest tests/visual/ (if layout/waveform/renderer geometry touched)
```

Write **why** in Summary; list commands actually run in Test plan.

### CI and review bots

Blocking jobs (must pass before merge):

| Job | What it runs |
|-----|----------------|
| `test (3.11)` | ruff + full pytest |
| `test (3.12)` | ruff + full pytest |
| `visual-golden` | `pytest tests/visual/` (Python 3.12, `manim==0.19.1`) |

**CodeRabbit** is informational. Triage as follows:

| Comment kind | Action |
|--------------|--------|
| **Actionable** (test leaks, correctness, would fail CI) | Fix and push |
| **Nitpick** (wording, formatting) | Fix if cheap; else defer with a PR comment |
| **Warning** (e.g. docstring coverage below threshold) | Not merge-blocking unless policy changes |
| **Architecture major** (e.g. stale ID cache vs live `Port.id`) | Follow semantic/core rules; document trade-off in PR |

**Project-specific regressions**:

- Tests touching [`animation/registry.py`](../../src/manim_engineering/animation/registry.py) must not leak into global `_REGISTRY` — use `monkeypatch` with a registry snapshot or explicit teardown.
- Changes to [`waveform/layout.py`](../../src/manim_engineering/waveform/layout.py) require full visual golden review (not SPI-only).

### Fix loop

1. `gh pr checks <number>` — wait for CI.
2. Read CodeRabbit summary and **actionable** inline comments.
3. Scoped fix commit → push. Do **not** `git commit --amend` after the branch is on the remote unless the user explicitly requests it and the commit was not pushed.
4. Repeat until merge criteria are met.

### Merge criteria and method

**Merge when**:

- `test (3.11)`, `test (3.12)`, and `visual-golden` are green
- No unresolved **actionable** review (or risk accepted in the PR thread)
- User has asked to merge (agents do not merge on their own initiative)

**Default**: `gh pr merge --squash --delete-branch`

**Forbidden** without explicit user request:

- force-push `main` / `master`
- merge while CI is red
- weakening CI workflows or test gates to make a PR pass

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

**Geometry golden discipline**: changes to `waveform/layout.py` (`step_polyline`, `panel_below_layout`), layout routing/engine wire or trace point lists, or pin anchors that shift routed geometry **must** refresh the full visual suite and review all `*.geometry.txt` diffs — see [docs/visual-validation.md](../../docs/visual-validation.md#geometry-golden-change-discipline).

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
