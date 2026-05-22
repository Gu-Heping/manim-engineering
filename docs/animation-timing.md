# Animation Timing Reference

Suggested durations for readable educational pacing. Motion philosophy: [`.cursor/rules/80-animation-and-education.md`](../.cursor/rules/80-animation-and-education.md).

## Duration guidelines

| Category | Seconds | Use |
|----------|---------|-----|
| Small emphasis | 0.3 – 0.6 | pin highlight, edge tick |
| Normal transition | 0.8 – 1.5 | signal step, local reveal |
| Important explanation | 1.5 – 3.0 | propagation across subsystem |
| Comprehension pause | 1.0 – 2.5+ | after major transition (no motion) |

Fast motion only when the concept is already established.

## Animation purpose tag

Each primitive should declare purpose (enforced in API design):

```text
propagation | timing | focus | transition
```

Decorative motion without a tag is disallowed.

## Progressive reveal order

1. global structure  
2. subsystem grouping  
3. active path  
4. local mechanism  
5. timing nuance  
6. edge cases  

## Reusable primitives (target names)

```python
SignalFlow(signal)
CurrentPulse(node)
VoltageGlow(node)
LogicTransition(gate)
WaveformSync(traces)
```

## Waveform sync

When semantic signal state changes, update in the same beat:

- wire highlight  
- waveform trace  
- dependent component state  

## Teaching density

At most **2** concepts per scene moment; **1** preferred.

## Educational scaling

Allowed: exaggerated delay, slowed clock, enlarged pulse — semantic ordering must stay correct.
