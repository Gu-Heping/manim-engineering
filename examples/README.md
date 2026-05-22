# Examples

Runnable scripts that demonstrate **one concept each**, aligned with [docs/ROADMAP.md](../docs/ROADMAP.md) phases. Examples respect layer boundaries: semantic first, then layout/render/animation only where noted.

## Directory map

| Directory | Focus | Phase |
|-----------|-------|-------|
| [basics/](basics/) | Graph, components, layout, render, animation, waveform | 1–6 |
| [analog/](analog/) | Analog circuits (placeholder) | — |
| [digital/](digital/) | Digital topology and propagation | 1, 8 |
| [protocol/](protocol/) | SPI/UART bus timing | 7–9 |
| [waveform/](waveform/) | Waveform traces and sync (index) | 6 |

## Prerequisites

```bash
pip install -e .
pip install -e ".[manim]"   # only for render / animation / Manim scene previews
```

## Running examples

**Smoke (no video)** — prints fixture output; works without Manim for most scripts:

```bash
python examples/basics/graph_only.py
python examples/basics/two_resistors_graph.py
python examples/basics/layout_two_resistors.py
python examples/basics/render_two_resistors.py
python examples/basics/signal_flow_demo.py
python examples/basics/clock_data_waveform.py
python examples/digital/logic_chain.py
python examples/protocol/spi_byte_transfer.py
python examples/protocol/uart_byte_transfer.py
```

**Manim preview** — low-quality preview (`-pql`); requires `manim` and a `Scene` class in the file:

```bash
manim -pql examples/basics/render_two_resistors.py RenderTwoResistors
manim -pql examples/basics/signal_flow_demo.py SignalFlowDemo
manim -pql examples/basics/clock_data_waveform.py ClockDataWaveformDemo
manim -pql examples/protocol/spi_byte_transfer.py SPIByteTransferDemo
manim -pql examples/protocol/uart_byte_transfer.py UARTByteTransferDemo
```

## Full catalog

### basics/

| Script | Concept | Key APIs |
|--------|---------|----------|
| `graph_only.py` | Topology + propagation + bus lane | `CircuitGraph`, `Node`, `Signal`, `Bus` |
| `two_resistors_graph.py` | Components on graph | `Resistor`, `CircuitGraph.connect` |
| `layout_two_resistors.py` | Grid placement + routing | `LayoutEngine`, `LayoutResult` |
| `render_two_resistors.py` | Minimal renderer | `MinimalRenderer.render_layout` |
| `signal_flow_demo.py` | Propagation animation | `SignalFlow` |
| `clock_data_waveform.py` | Clock/data + waveform panel | `derive_bundle_from_signals`, `WaveformSync` |

See [basics/README.md](basics/README.md).

### digital/

| Script | Concept | Key APIs |
|--------|---------|----------|
| `logic_chain.py` | Digital chain propagation | `CircuitGraph`, `Signal.propagate` |

See [digital/README.md](digital/README.md).

### protocol/

| Script | Concept | Key APIs |
|--------|---------|----------|
| `spi_byte_transfer.py` | SPI mode-0 byte + waveforms | `SPIController`, `SPIBusBinding`, `WaveformSync` |
| `uart_byte_transfer.py` | UART 8N1 TX + waveforms | `UARTController`, `UARTBinding`, `WaveformSync` |

See [protocol/README.md](protocol/README.md).

### analog/ · waveform/

Analog component examples are deferred — see [analog/README.md](analog/README.md).  
Waveform-focused runs are indexed in [waveform/README.md](waveform/README.md) (canonical script: `basics/clock_data_waveform.py`).
