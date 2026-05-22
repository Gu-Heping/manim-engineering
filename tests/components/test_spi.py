"""SPI interface component pin contract."""

from __future__ import annotations

from manim_engineering.components import SPIMaster, SPISlave
from manim_engineering.semantic import PinDirection, SignalType


def test_spi_master_pins() -> None:
    master = SPIMaster("m1", label="MCU")
    assert master.get_pin("clk").direction is PinDirection.OUT
    assert master.get_pin("mosi").signal_type is SignalType.DATA
    assert master.get_pin("miso").direction is PinDirection.IN


def test_spi_slave_pins() -> None:
    slave = SPISlave("s1", label="SLV")
    assert slave.get_pin("miso").direction is PinDirection.OUT
    assert slave.get_pin("clk").direction is PinDirection.IN
