# Analog examples

**Status:** deferred — no analog-specific example scripts yet.

Planned content (post–Phase 8 backlog):

- Op-amp or RC network as `CircuitElement` stubs
- Semantic nodes for analog nets (voltage as state, not SPICE)
- Layout + minimal render once analog symbols exist in `renderers/minimal/`

## Related today

Passive symbols used in basics (`Resistor`, `Capacitor` in `components/passive/`) appear in:

- `examples/basics/two_resistors_graph.py`
- `examples/basics/layout_two_resistors.py`
- `examples/basics/render_two_resistors.py`

Those illustrate component + layout patterns that analog scenes will reuse.
