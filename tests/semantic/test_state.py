"""LogicState and TimingEvent tests."""

from __future__ import annotations

from manim_engineering.semantic import LogicLevel, LogicState, TimingEdge, TimingEvent


def test_logic_state_transition_label() -> None:
    low = LogicState(level=LogicLevel.LOW)
    high = LogicState(level=LogicLevel.HIGH, voltage=3.3)
    assert low.transition_label(high) == "low→high"


def test_logic_state_repr_omits_none_voltage() -> None:
    assert repr(LogicState(level=LogicLevel.LOW)) == "LogicState(level=<LogicLevel.LOW: 'low'>)"
    assert "voltage" in repr(LogicState(level=LogicLevel.HIGH, voltage=3.3))


def test_timing_event_construction() -> None:
    event = TimingEvent(time=1.5, edge=TimingEdge.RISING, pin_id="u1.clk", metadata={"skew": 0.1})
    assert event.edge == TimingEdge.RISING
    assert event.metadata["skew"] == 0.1
