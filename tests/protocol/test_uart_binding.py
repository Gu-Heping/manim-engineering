"""UART binding to circuit graph nodes."""

from __future__ import annotations

from manim_engineering.components import UARTPort
from manim_engineering.core import CircuitGraph
from manim_engineering.protocol.uart import UARTBinding


def test_from_graph_nodes_connects_tx_to_rx() -> None:
    graph = CircuitGraph()
    UARTPort("tx_dev", label="MCU TX").attach_to(graph)
    UARTPort("rx_dev", label="HOST RX").attach_to(graph)
    binding = UARTBinding.from_graph_nodes(
        graph,
        transmitter_id="tx_dev",
        receiver_id="rx_dev",
    )
    assert len(graph.connections) == 1
    assert binding.tx.name == "tx"
    assert binding.signals()[0] is binding.tx
