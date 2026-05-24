# Component API Reference

Executable contract for `components/`. Rules: [`.cursor/rules/70-component-authoring.md`](../.cursor/rules/70-component-authoring.md).

## Base class

```python
class CircuitElement:
    label: str | None
    pins: dict[str, Pin]
    semantic_type: str
    anchor_points: ...
    bounds: ...
```

All components **must** inherit `CircuitElement`.

## Required surface

| Member | Required | Notes |
|--------|----------|-------|
| `label` | optional | `Resistor()` and `Resistor(label="R1")` both valid |
| `pins` | yes for connectable | See pin naming below |
| `semantic_type` | yes | e.g. `passive`, `analog`, `digital`, `power`, `interface` |
| `anchor_points` | yes | For layout alignment |
| `bounds` | yes | For routing and camera |

## Required methods

```python
def get_pin(self, name: str) -> Pin: ...
def get_bounds(self) -> Bounds: ...
```

`render()` is **not** on the component — use `renderer.render(component)`.

## Pin naming

Lowercase, stable engineering names:

```text
gate, source, drain, vcc, gnd, clk, rst, tx, rx, in, out
```

## Categories

| Directory      | Status      | Examples |
|----------------|-------------|----------|
| `passive/`     | implemented | Resistor, Capacitor, Inductor |
| `common/`      | implemented | Ground, VCC, InputDriver (single-pin OUT stimulus marker, `semantic_type="io"`) |
| `digital/`     | implemented | SPIMaster, SPISlave, UARTPort |
| `analog/`      | implemented | NMOS, PMOS, Diode, OpAmp, NPN, PNP, ZenerDiode |
| `measurement/` | planned     | probes, meters |

`planned` directories are described in the roadmap backlog and do not yet
exist in source — do not import from them.

## Forbidden on components

```python
scene.play(...)              # scenes only
self.stroke_color = BLUE     # renderer theme
mos.animate_signal()         # use SignalFlow(mos)
if renderer == "ieee": ...    # renderer external
component[3][1][5]            # use get_pin("gate")
```

## State

May expose semantic state: `logic_state`, `voltage`, `enabled`, `selected_input`.

Must not own: animation state, renderer style, simulation scheduler.

## Tests (per component)

- construction
- pin existence and names
- bounds valid
- renderer compatibility (smoke)
- layout hints present

## Granularity

Prefer `NMOS`, `ANDGate` over `EntireCPU`, `MegaMotherboard`.
