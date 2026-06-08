from __future__ import annotations

import pytest

from manim_engineering import build_circuit
from manim_engineering.components import Ground, Resistor
from manim_engineering.core import InvalidConnectionError, InvalidPortError
from manim_engineering.quickstart import BuildParameterError


def test_build_circuit_registers_elements_and_connections() -> None:
    r1 = Resistor("r1", label="R1")
    gnd = Ground("gnd1", label="GND")

    result = build_circuit(
        {"r1": r1, "gnd1": gnd},
        [("r1", "b", "gnd1", "gnd")],
    )

    assert tuple(node.id for node in result.graph.nodes) == ("gnd1", "r1")
    assert tuple(conn.id for conn in result.graph.connections) == ("conn-gnd1.gnd--r1.b",)
    assert result.elements["r1"] is r1
    assert result.connections == (("r1", "b", "gnd1", "gnd"),)


def test_build_circuit_accepts_ordered_sequence_input() -> None:
    r1 = Resistor("r1")
    r2 = Resistor("r2")

    result = build_circuit(
        [("r1", r1), ("r2", r2)],
        [("r1", "b", "r2", "a")],
    )

    assert set(result.elements) == {"r1", "r2"}
    assert result.graph.are_connected(r1.get_port("b"), r2.get_port("a"))


def test_build_circuit_rejects_element_id_mismatch() -> None:
    with pytest.raises(BuildParameterError, match="element id mismatch"):
        build_circuit([("alias", Resistor("r1"))], [])


def test_build_circuit_rejects_duplicate_element_id_sequence() -> None:
    with pytest.raises(BuildParameterError, match="duplicate element id"):
        build_circuit([("r1", Resistor("r1")), ("r1", Resistor("r1"))], [])


def test_build_circuit_rejects_unknown_connection_endpoint() -> None:
    r1 = Resistor("r1")

    with pytest.raises(
        InvalidConnectionError,
        match=r"invalid connection r1\.b -> missing\.a: unknown target element 'missing'",
    ):
        build_circuit({"r1": r1}, [("r1", "b", "missing", "a")])


def test_build_circuit_rejects_unknown_port_name() -> None:
    r1 = Resistor("r1")
    r2 = Resistor("r2")

    with pytest.raises(InvalidPortError, match="invalid connection r1\\.missing -> r2\\.a"):
        build_circuit({"r1": r1, "r2": r2}, [("r1", "missing", "r2", "a")])
