"""SPI bus binding to circuit graph nodes."""

from __future__ import annotations

from manim_engineering.components import SPIMaster, SPISlave
from manim_engineering.core import CircuitGraph
from manim_engineering.protocol.spi import SPIBusBinding


def test_from_graph_nodes_connects_four_lines() -> None:
    graph = CircuitGraph()
    SPIMaster("master").attach_to(graph)
    SPISlave("slave").attach_to(graph)
    binding = SPIBusBinding.from_graph_nodes(graph, master_id="master", slave_id="slave")
    assert len(graph.connections) == 4
    assert binding.clk.name == "clk"
    assert binding.signals()[0] is binding.clk
