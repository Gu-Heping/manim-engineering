"""Bind SPI bus signals to a circuit graph and named pins."""

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
class SPIBusBinding:
    """
    SPI clk/mosi/miso/cs signals wired between master and slave nodes.

    Master drives clk, mosi, cs; slave drives miso during transmit.
    """

    graph: CircuitGraph
    master_clk: Pin
    master_mosi: Pin
    master_miso: Pin
    master_cs: Pin
    slave_clk: Pin
    slave_mosi: Pin
    slave_miso: Pin
    slave_cs: Pin
    clk: Signal
    mosi: Signal
    miso: Signal
    cs: Signal

    @classmethod
    def from_graph_nodes(
        cls,
        graph: CircuitGraph,
        *,
        master_id: str,
        slave_id: str,
    ) -> SPIBusBinding:
        """Wire SPI lines between registered master/slave nodes (e.g. after ``attach_to``)."""
        master = graph.get_node(master_id)
        slave = graph.get_node(slave_id)

        m_clk = master.get_pin("clk")
        m_mosi = master.get_pin("mosi")
        m_miso = master.get_pin("miso")
        m_cs = master.get_pin("cs")
        s_clk = slave.get_pin("clk")
        s_mosi = slave.get_pin("mosi")
        s_miso = slave.get_pin("miso")
        s_cs = slave.get_pin("cs")

        for pin_a, pin_b in (
            (m_clk, s_clk),
            (m_mosi, s_mosi),
            (m_miso, s_miso),
            (m_cs, s_cs),
        ):
            if not graph.are_connected(pin_a, pin_b):
                graph.connect(pin_a, pin_b)

        return cls._with_signals(
            graph,
            m_clk,
            m_mosi,
            m_miso,
            m_cs,
            s_clk,
            s_mosi,
            s_miso,
            s_cs,
        )

    @classmethod
    def create_bus(
        cls,
        graph: CircuitGraph,
        *,
        master_id: str = "master",
        slave_id: str = "slave",
        master_label: str = "MCU",
        slave_label: str = "SLV",
    ) -> SPIBusBinding:
        """Register bare master/slave nodes (tests) and connect SPI lines."""
        master = Node(id=master_id, label=master_label)
        slave = Node(id=slave_id, label=slave_label)

        master.add_pin("clk", direction=PinDirection.OUT, signal_type=SignalType.CLOCK)
        master.add_pin("mosi", direction=PinDirection.OUT, signal_type=SignalType.DATA)
        master.add_pin("miso", direction=PinDirection.IN, signal_type=SignalType.DATA)
        master.add_pin("cs", direction=PinDirection.OUT, signal_type=SignalType.DIGITAL)

        slave.add_pin("clk", direction=PinDirection.IN, signal_type=SignalType.CLOCK)
        slave.add_pin("mosi", direction=PinDirection.IN, signal_type=SignalType.DATA)
        slave.add_pin("miso", direction=PinDirection.OUT, signal_type=SignalType.DATA)
        slave.add_pin("cs", direction=PinDirection.IN, signal_type=SignalType.DIGITAL)

        graph.add_node(master)
        graph.add_node(slave)

        m_clk = master.get_pin("clk")
        m_mosi = master.get_pin("mosi")
        m_miso = master.get_pin("miso")
        m_cs = master.get_pin("cs")
        s_clk = slave.get_pin("clk")
        s_mosi = slave.get_pin("mosi")
        s_miso = slave.get_pin("miso")
        s_cs = slave.get_pin("cs")

        graph.connect(m_clk, s_clk)
        graph.connect(m_mosi, s_mosi)
        graph.connect(m_miso, s_miso)
        graph.connect(m_cs, s_cs)

        return cls._with_signals(
            graph,
            m_clk,
            m_mosi,
            m_miso,
            m_cs,
            s_clk,
            s_mosi,
            s_miso,
            s_cs,
        )

    @classmethod
    def _with_signals(
        cls,
        graph: CircuitGraph,
        m_clk: Pin,
        m_mosi: Pin,
        m_miso: Pin,
        m_cs: Pin,
        s_clk: Pin,
        s_mosi: Pin,
        s_miso: Pin,
        s_cs: Pin,
    ) -> SPIBusBinding:
        idle = LogicState(level=LogicLevel.HIGH)
        clk = Signal(
            name="clk",
            signal_type=SignalType.CLOCK,
            value=LogicState(level=LogicLevel.LOW),
        )
        mosi = Signal(name="mosi", signal_type=SignalType.DATA, value=idle)
        miso = Signal(name="miso", signal_type=SignalType.DATA, value=idle)
        cs = Signal(name="cs", signal_type=SignalType.DIGITAL, value=idle)

        return cls(
            graph=graph,
            master_clk=m_clk,
            master_mosi=m_mosi,
            master_miso=m_miso,
            master_cs=m_cs,
            slave_clk=s_clk,
            slave_mosi=s_mosi,
            slave_miso=s_miso,
            slave_cs=s_cs,
            clk=clk,
            mosi=mosi,
            miso=miso,
            cs=cs,
        )

    def signals(self) -> tuple[Signal, Signal, Signal, Signal]:
        """Bus signals in stable order: clk, mosi, miso, cs."""
        return (self.clk, self.mosi, self.miso, self.cs)
