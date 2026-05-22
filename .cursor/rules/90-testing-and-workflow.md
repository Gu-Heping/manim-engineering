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

**Implementation order**:

1. semantic definition  
2. component definition  
3. rendering support  
4. animation support  
5. tests  
6. examples  

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

## CI

Tests run in CI: imports, rendering stability, API compatibility, basic examples. Broken CI is blocking.

## Performance

No premature optimization. Flag exponential layout, runaway animation cost, accidental quadratic patterns.
