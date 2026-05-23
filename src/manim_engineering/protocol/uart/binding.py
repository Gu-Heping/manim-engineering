"""Bind UART TX/RX signals to a circuit graph and named pins."""

from __future__ import annotations

from dataclasses import dataclass

from manim_engineering.core import (
    CircuitGraph,
    Node,
    Pin,
    PinDirection,
    SignalType,
)
from manim_engineering.semantic import LogicLevel, LogicState, Signal


@dataclass
class UARTBinding:
    """
    UART line between transmitter TX and receiver RX.

    Transmitter drives ``tx`` during a frame; receiver listens on the same wire.
    """

    graph: CircuitGraph
    transmitter_tx: Pin
    receiver_rx: Pin
    tx: Signal

    @classmethod
    def from_graph_nodes(
        cls,
        graph: CircuitGraph,
        *,
        transmitter_id: str,
        receiver_id: str,
    ) -> UARTBinding:
        """Wire TX→RX between registered nodes (e.g. after ``attach_to``)."""
        transmitter = graph.get_node(transmitter_id)
        receiver = graph.get_node(receiver_id)

        t_tx = transmitter.get_pin("tx")
        r_rx = receiver.get_pin("rx")

        if not graph.are_connected(t_tx, r_rx):
            graph.connect(t_tx, r_rx)

        return cls._with_signals(graph, t_tx, r_rx)

    @classmethod
    def create_bus(
        cls,
        graph: CircuitGraph,
        *,
        transmitter_id: str = "tx",
        receiver_id: str = "rx",
        transmitter_label: str = "TX",
        receiver_label: str = "RX",
    ) -> UARTBinding:
        """Register bare transmitter/receiver nodes (tests) and connect the line."""
        transmitter = Node(id=transmitter_id, label=transmitter_label)
        receiver = Node(id=receiver_id, label=receiver_label)

        transmitter.add_pin("tx", direction=PinDirection.OUT, signal_type=SignalType.DATA)
        receiver.add_pin("rx", direction=PinDirection.IN, signal_type=SignalType.DATA)

        graph.add_node(transmitter)
        graph.add_node(receiver)

        t_tx = transmitter.get_pin("tx")
        r_rx = receiver.get_pin("rx")
        graph.connect(t_tx, r_rx)

        return cls._with_signals(graph, t_tx, r_rx)

    @classmethod
    def _with_signals(
        cls,
        graph: CircuitGraph,
        transmitter_tx: Pin,
        receiver_rx: Pin,
    ) -> UARTBinding:
        idle = LogicState(level=LogicLevel.HIGH)
        tx = Signal(name="tx", signal_type=SignalType.DATA, value=idle)
        return cls(
            graph=graph,
            transmitter_tx=transmitter_tx,
            receiver_rx=receiver_rx,
            tx=tx,
        )

    def signals(self) -> tuple[Signal, ...]:
        """Bus signals in stable order: tx line."""
        return (self.tx,)
