"""Guard against ``semantic`` re-exporting topology types.

Topology lives in ``manim_engineering.core``. The semantic layer owns
logic levels, signals, buses, propagation, timing — *consumers* of the
topology, never an alternative entry point to it.

If any of these guards fail, you almost certainly accidentally re-added a
shim (e.g. ``semantic/graph.py``) or re-exported a topology name from
``semantic/__init__.py`` or ``semantic/enums.py``.
"""

from __future__ import annotations

import pytest

# Topology names that used to be re-exported by ``semantic`` but no longer
# should be. ``Bus`` is intentionally absent — it *is* a semantic concept
# even though it groups topology pins.
TOPOLOGY_NAMES: tuple[str, ...] = (
    "CircuitGraph",
    "Node",
    "Pin",
    "Port",
    "Connection",
    "PinDirection",
    "PortDirection",
    "ConnectionState",
    "SignalType",
    "TopologyError",
    "InvalidConnectionError",
    "InvalidPortError",
)


@pytest.mark.parametrize("name", TOPOLOGY_NAMES)
def test_semantic_package_does_not_reexport_topology(name: str) -> None:
    import manim_engineering.semantic as semantic

    assert not hasattr(semantic, name), (
        f"semantic re-exports {name!r}; topology types must come from "
        f"manim_engineering.core only. Remove the re-export from "
        f"semantic/__init__.py."
    )


@pytest.mark.parametrize(
    "name",
    ("SignalType", "PinDirection", "PortDirection", "ConnectionState"),
)
def test_semantic_enums_module_does_not_reexport_core_enums(name: str) -> None:
    import manim_engineering.semantic.enums as semantic_enums

    assert not hasattr(semantic_enums, name), (
        f"semantic.enums re-exports {name!r}; core enums must come from "
        f"manim_engineering.core.enums only."
    )


def test_semantic_does_not_expose_deleted_shim_modules() -> None:
    """``import manim_engineering.semantic.graph`` etc. must fail outright."""
    import importlib

    for shim in ("graph", "node", "pin", "connection"):
        with pytest.raises(ModuleNotFoundError):
            importlib.import_module(f"manim_engineering.semantic.{shim}")


def test_core_owns_all_topology_names() -> None:
    """All topology names this guard tracks must be importable from core."""
    import manim_engineering.core as core

    for name in TOPOLOGY_NAMES:
        assert hasattr(core, name), (
            f"core is missing {name!r}; topology types must live in core and only there."
        )


def test_no_topology_test_files_remain_in_semantic() -> None:
    """Reverse guard for E-2: no file in ``tests/semantic/`` may live there

    without importing at least one symbol owned by ``manim_engineering.semantic``.
    A file that only imports from ``manim_engineering.core`` is a topology
    test that belongs in ``tests/core/`` — the A+B+D follow-up moved several
    such files (``test_graph.py`` → ``test_graph_topology.py``,
    ``test_pin_node.py`` → ``test_node_pin.py``, the topology half of
    ``test_determinism.py`` → ``test_graph_determinism.py``); this guard
    prevents the regression.
    """
    import ast
    from pathlib import Path

    semantic_tests_dir = Path(__file__).resolve().parents[1] / "semantic"
    assert semantic_tests_dir.is_dir(), f"missing {semantic_tests_dir}"

    offenders: list[str] = []
    for py_file in sorted(semantic_tests_dir.glob("test_*.py")):
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_file))
        has_semantic_import = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module == "manim_engineering.semantic" or node.module.startswith(
                    "manim_engineering.semantic."
                ):
                    has_semantic_import = True
                    break
        if not has_semantic_import:
            offenders.append(py_file.name)

    assert not offenders, (
        "Files in tests/semantic/ that do not import from "
        "manim_engineering.semantic are topology tests; move them to "
        "tests/core/:\n  - " + "\n  - ".join(offenders)
    )
