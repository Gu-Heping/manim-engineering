# Digital examples

Digital topology and signal propagation without analog or protocol framing.

## Table

| File | Concept | Key abstractions |
|------|---------|------------------|
| `logic_chain.py` | Three-node chain, single `propagate` | `CircuitGraph`, `Node`, `Signal`, `LogicState` |

## Related in basics/

| File | Why |
|------|-----|
| `graph_only.py` | Same layer with `Bus`, clock-type `Signal`, second hop |
| `clock_data_waveform.py` | Clock + data types, waveform derivation |
| `signal_flow_demo.py` | Propagation animation on a routed net |

## Run commands

```bash
python examples/digital/logic_chain.py
```

No Manim scene in this directory yet; gate symbols and `SignalFlow` on digital graphs are backlog items.
