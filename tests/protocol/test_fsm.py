"""SPI FSM determinism and ownership."""

from __future__ import annotations

import pytest

from manim_engineering.protocol.spi.enums import SPIBusOwner, SPIFsmState
from manim_engineering.protocol.spi.fsm import (
    owner_for_line,
    transition_on_cs_assert,
    transition_on_cs_deassert,
    transition_on_first_clock_edge,
)


def test_cs_assert_idle_to_active() -> None:
    assert transition_on_cs_assert(SPIFsmState.IDLE) is SPIFsmState.ACTIVE


def test_cs_assert_invalid_from_transmitting() -> None:
    with pytest.raises(ValueError):
        transition_on_cs_assert(SPIFsmState.TRANSMITTING)


def test_first_clock_active_to_transmitting() -> None:
    assert transition_on_first_clock_edge(SPIFsmState.ACTIVE) is SPIFsmState.TRANSMITTING


def test_clock_while_transmitting_stays() -> None:
    assert transition_on_first_clock_edge(SPIFsmState.TRANSMITTING) is SPIFsmState.TRANSMITTING


def test_cs_deassert_returns_idle() -> None:
    assert transition_on_cs_deassert(SPIFsmState.TRANSMITTING) is SPIFsmState.IDLE
    assert transition_on_cs_deassert(SPIFsmState.ACTIVE) is SPIFsmState.IDLE


def test_master_owns_clk_mosi_cs_when_active() -> None:
    assert owner_for_line("clk", SPIFsmState.ACTIVE) is SPIBusOwner.MASTER
    assert owner_for_line("mosi", SPIFsmState.ACTIVE) is SPIBusOwner.MASTER
    assert owner_for_line("cs", SPIFsmState.ACTIVE) is SPIBusOwner.MASTER


def test_slave_owns_miso_while_transmitting() -> None:
    assert owner_for_line("miso", SPIFsmState.TRANSMITTING) is SPIBusOwner.SLAVE
    assert owner_for_line("miso", SPIFsmState.IDLE) is SPIBusOwner.NONE
