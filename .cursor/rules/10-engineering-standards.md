# Engineering Standards

Code, API, and visual conventions. Applies after `00-foundation` layer rules.

## Code

- One responsibility per function/class; shallow inheritance; composition preferred
- Explicit state; no hidden mutation, global state, or `except: pass`
- Type hints on public APIs; prefer dataclasses for structured data
- Focused modules; no god objects, renderer-animation hybrids, or domain-mixed files
- No `utils.py` / `helper.py` dumping grounds
- Dependencies justified; no premature optimization

**Naming**: concise, engineering-oriented, stable.

Good: `SignalFlow`, `CircuitGraph`, `LogicState`  
Bad: `MagicHelper`, `SmartRenderer`, `UltimateCircuit`, `HyperAnimator`

## API

- Small, explicit, composable, predictable constructors
- Behavior via explicit calls (`SignalFlow(signal)`), not `enable_everything()` magic
- Renderer selection: `renderer.render(component)` — never `NMOS(renderer="ieee")`
- Animation: external composition (`SignalFlow(mos)`), never `component.animate_signal()`
- Errors: raise typed exceptions (`InvalidPinError`, `InvalidConnectionError`)

## Visual Style (renderer-owned)

Renderers apply style; components stay style-free.

**Geometry**: orthogonal routing, grid alignment, straight lines; no chaotic curves or arbitrary placement.

**Theme mapping** (via renderer theme, not semantic fields):

| Signal kind | Default color |
|-------------|---------------|
| POWER | RED |
| GROUND | GREY |
| CLOCK | YELLOW |
| DATA | GREEN |
| SIGNAL | BLUE |

Semantic layer MUST NOT set `color`, `stroke_width`, or visual properties.

**Motion** (animation layer): restrained pacing; no overlapping highlights, flashing, or decorative motion.

**Typography**: clean sans-serif, consistent sizing; no decorative fonts or label clutter.

## Architecture Violations (forbidden patterns)

```python
# semantic styling
signal.color = RED

# renderer in component
NMOS(renderer="ieee")

# animation on component
mos.animate_signal()

# geometry-based topology
if line.intersects(other): ...

# silent failure
except:
    pass
```

## Review Checklist (significant changes)

1. layer boundaries intact
2. naming consistent with existing APIs
3. no duplication of existing abstractions
4. deterministic behavior
5. tests and minimal example included
