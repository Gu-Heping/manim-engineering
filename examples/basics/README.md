# Basics examples

Foundation vertical slice: semantic graph → passive components → layout → minimal render → animation → waveform. One script per phase milestone.

## Table

| File | Phase | Concept | Key abstractions |
|------|-------|---------|------------------|
| `graph_only.py` | 1 | Build graph, propagate digital edge, bus lane | `CircuitGraph`, `Node`, `Pin`, `Signal`, `Bus` |
| `two_resistors_graph.py` | 2 | Two `Resistor` elements wired in graph | `CircuitElement.attach_to`, `get_pin`, `connect` |
| `layout_two_resistors.py` | 3 | Grid placement, orthogonal wires, occupancy | `LayoutEngine`, `LayoutResult` |
| `render_two_resistors.py` | 4 | Static Manim group from layout | `MinimalRenderer.render_layout` |
| `signal_flow_demo.py` | 5 | Highlight propagation along routed net | `SignalFlow`, `Signal.propagate` |
| `clock_data_waveform.py` | 6 | Clock + data traces, panel, timing sync | `derive_bundle_from_signals`, `WaveformPanelRenderer`, `WaveformSync` |

## Run commands

No Manim required (smoke):

```bash
python examples/basics/graph_only.py
python examples/basics/two_resistors_graph.py
python examples/basics/layout_two_resistors.py
python examples/basics/render_two_resistors.py
python examples/basics/signal_flow_demo.py
python examples/basics/clock_data_waveform.py
```

Manim preview (install `pip install -e ".[manim]"` first):

```bash
manim -pql examples/basics/render_two_resistors.py RenderTwoResistors
manim -pql examples/basics/signal_flow_demo.py SignalFlowDemo
manim -pql examples/basics/clock_data_waveform.py ClockDataWaveformDemo
```

`render_two_resistors.py` and `signal_flow_demo.py` also expose `main()` for structure checks without opening a preview window.
