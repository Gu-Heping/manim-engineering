# KNOWN_PROBLEMS (for AI engineers)

## 1) Animation reveal path is still partially transitional

- Intro baseline path and beat reveal path are separate orchestration paths.
- `restore_waveform_strokes` still participates in reveal persistence logic.
- Controller facade exists but not all orchestration paths are controller-native.

Impact: cognitive complexity for maintainers; higher risk of reintroducing reveal regressions.

## 2) Legacy compatibility surface increases navigation cost

- Backward-compatible aliases and multiple entry points remain by design.
- New contributors can accidentally patch compatibility path instead of canonical path.

Impact: slower debugging and occasional duplicated logic.

## 3) Scope mismatch risk: “physics expectation” vs teaching abstraction

- Scenes visually suggest engineering behavior but do not run full physical simulation.
- New contributors may overextend into solver features without semantic foundation.

Impact: architecture drift if not constrained.

## 4) Layout auto-placement pressure vs preset-first policy

- Users naturally request global auto-placer behavior.
- Current policy intentionally resists opaque default solvers.

Impact: repeated pressure to bypass explainability requirements.

## 5) Manim caching can mask framework changes

- Developers can misread stale output as logic failure/success.

Impact: false debugging conclusions unless `--disable_caching` is used.

## 6) Scene-level visual tweaks can violate contracts quickly

- Group opacity/fade shortcuts on mixed mobject trees can break stroke/fill persistence.

Impact: abrupt pops, ghost labels, and non-deterministic appearance bugs.

