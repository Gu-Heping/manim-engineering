# Basics examples

Foundation vertical slice: semantic graph → passive components → layout → minimal render → animation → waveform. One script per phase milestone.

## Table

| File | Phase | Concept | Key abstractions |
|------|-------|---------|------------------|
| `graph_only.py` | 1 | Build graph, propagate digital edge, bus lane | `CircuitGraph`, `Node`, `Pin`, `Signal`, `Bus` |
| `two_resistors_graph.py` | 2 | Two `Resistor` elements wired in graph | `CircuitElement.attach_to`, `get_pin`, `connect` |
| `layout_two_resistors.py` | 3 | Grid placement, orthogonal wires, occupancy | `LayoutEngine`, `LayoutResult` |
| `render_two_resistors.py` | 4 | Static Manim group from layout | `MinimalRenderer.render_layout` |
| `signal_flow_demo.py` | 5 | Highlight propagation along routed net | `play_propagation_beat`, `Signal.propagate` |
| `clock_data_waveform.py` | 6 / acceptance | DRV–RCV **separate** clk + data nets, four beats, progressive reveal | `play_propagation_beat`, `WaveformRevealTracker`, pacing constants |
| `signal_chain_demo.py` | 6 | Three-resistor chain: **net12** on R1–R2, **net23** on R2–R3 (segment edges, not clk/data) | `record_rising_edge`, `SignalChainDemo` |
| `acceptance_three_layer.py` | 3-layer | **InputDriver→R1→C1→GND** two-beat edge path | `CircuitGraph`, `ManimRenderer`, `PropagationSequence` |
| `governance_acceptance.py` | governance | Same RC topology + waveform band + progressive reveal | `WaveformRevealTracker`, `scene_frame_bounds` |

## Run commands

No Manim required (smoke):

```bash
python examples/basics/graph_only.py
python examples/basics/two_resistors_graph.py
python examples/basics/layout_two_resistors.py
python examples/basics/render_two_resistors.py
python examples/basics/signal_flow_demo.py
python examples/basics/clock_data_waveform.py
python examples/basics/signal_chain_demo.py
python examples/basics/acceptance_three_layer.py
python examples/basics/governance_acceptance.py
```

Manim preview (install `pip install -e ".[manim]"` first):

```bash
manim -pql examples/basics/render_two_resistors.py RenderTwoResistors
manim -pql examples/basics/signal_flow_demo.py SignalFlowDemo
manim -pql examples/basics/clock_data_waveform.py ClockDataWaveformDemo
manim -pql examples/basics/signal_chain_demo.py SignalChainDemo
manim -pql examples/basics/acceptance_three_layer.py AcceptanceScene
manim -pql examples/basics/governance_acceptance.py GovernanceAcceptanceScene
```

Scenes use `manim_engineering.animation.pacing` (`INTRO_PAUSE`, `BEAT_DURATION`, `BEAT_GAP`, `OUTRO_PAUSE`) and either **`play_propagation_beat`** (single beat) or **`PropagationSequence(beats=...)`** (multi-beat, optionally with HUD captions via `subtitle_text` + `caption_callback`) so wire pulses and waveform edge flashes share one `run_time`. Camera setup goes through `configure_waveform_scene_camera(self, layout, panel_spec, bundle)`. See [`docs/animation-timing.md`](../../docs/animation-timing.md).

Medium-quality acceptance renders (~10–15 s, export `acceptance_*_frame.png`):

```bash
manim -qm examples/basics/clock_data_waveform.py ClockDataWaveformDemo
manim -qm examples/basics/signal_chain_demo.py SignalChainDemo
manim -qm examples/basics/governance_acceptance.py GovernanceAcceptanceScene
```

Low-quality render (no preview window):

```bash
manim -ql examples/basics/acceptance_three_layer.py AcceptanceScene
manim -ql examples/basics/governance_acceptance.py GovernanceAcceptanceScene
```

`render_two_resistors.py` and `signal_flow_demo.py` also expose `main()` for structure checks without opening a preview window.
