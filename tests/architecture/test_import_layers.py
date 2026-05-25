"""Architecture tests: import direction matches layer model in 00-foundation.md."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "manim_engineering"
PACKAGE_ROOT = "manim_engineering"

# Forbidden import prefixes per layer (lower must not depend on upper).
LAYER_FORBIDDEN_PREFIXES: dict[str, tuple[str, ...]] = {
    "core": (
        "manim",
        f"{PACKAGE_ROOT}.debug",
        f"{PACKAGE_ROOT}.components",
        f"{PACKAGE_ROOT}.layout",
        f"{PACKAGE_ROOT}.protocol",
        f"{PACKAGE_ROOT}.waveform",
        f"{PACKAGE_ROOT}.renderers",
        f"{PACKAGE_ROOT}.animation",
        f"{PACKAGE_ROOT}.semantic",
    ),
    "semantic": (
        "manim",
        f"{PACKAGE_ROOT}.debug",
        f"{PACKAGE_ROOT}.components",
        f"{PACKAGE_ROOT}.layout",
        f"{PACKAGE_ROOT}.protocol",
        f"{PACKAGE_ROOT}.waveform",
        f"{PACKAGE_ROOT}.renderers",
        f"{PACKAGE_ROOT}.animation",
    ),
    "protocol": (
        "manim",
        f"{PACKAGE_ROOT}.debug",
        f"{PACKAGE_ROOT}.components",
        f"{PACKAGE_ROOT}.layout",
        f"{PACKAGE_ROOT}.waveform",
        f"{PACKAGE_ROOT}.renderers",
        f"{PACKAGE_ROOT}.animation",
    ),
    "components": (
        "manim",
        f"{PACKAGE_ROOT}.debug",
        f"{PACKAGE_ROOT}.layout",
        f"{PACKAGE_ROOT}.renderers",
        f"{PACKAGE_ROOT}.animation",
    ),
    "layout": (
        "manim",
        f"{PACKAGE_ROOT}.debug",
        f"{PACKAGE_ROOT}.renderers",
        f"{PACKAGE_ROOT}.animation",
    ),
    "waveform": (
        "manim",
        f"{PACKAGE_ROOT}.debug",
        f"{PACKAGE_ROOT}.animation",
    ),
    "renderers": (f"{PACKAGE_ROOT}.animation", f"{PACKAGE_ROOT}.debug"),
    "animation": (),
}


def _iter_python_files(package_dir: Path) -> list[Path]:
    return sorted(package_dir.rglob("*.py"))


def _collect_imported_modules(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            modules.add(node.module)
    return modules


@pytest.mark.parametrize("layer,forbidden", list(LAYER_FORBIDDEN_PREFIXES.items()))
def test_layer_import_direction(layer: str, forbidden: tuple[str, ...]) -> None:
    package_dir = SRC_ROOT / layer
    assert package_dir.is_dir(), f"missing layer package: {layer}"

    violations: list[str] = []
    for py_file in _iter_python_files(package_dir):
        rel = py_file.relative_to(SRC_ROOT)
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_file))
        for imported in _collect_imported_modules(tree):
            for prefix in forbidden:
                if imported == prefix or imported.startswith(f"{prefix}."):
                    violations.append(f"{rel}: imports {imported} (forbidden: {prefix})")

    assert not violations, "Import direction violations:\n" + "\n".join(violations)


def test_all_layer_packages_exist() -> None:
    missing = [name for name in LAYER_FORBIDDEN_PREFIXES if not (SRC_ROOT / name).is_dir()]
    assert not missing, f"missing layer packages: {missing}"


def test_layer_packages_importable() -> None:
    import importlib

    for layer in LAYER_FORBIDDEN_PREFIXES:
        importlib.import_module(f"{PACKAGE_ROOT}.{layer}")


def test_core_is_topology_only_entry() -> None:
    """Core public API exposes graph model without semantic signal types."""
    from manim_engineering import core

    assert hasattr(core, "CircuitGraph")
    assert hasattr(core, "Port")
    assert not hasattr(core, "Signal")


# Modules that were deleted as part of the semantic/core de-duplication. These
# were thin re-export shims that aliased ``core.graph.CircuitGraph`` etc. under
# the ``semantic`` namespace. Re-adding any of them would silently re-introduce
# the double-entry that the architecture audit removed — this guard runs at
# every CI cycle so the regression cannot land.
DELETED_SEMANTIC_TOPOLOGY_MODULES: tuple[str, ...] = (
    f"{PACKAGE_ROOT}.semantic.graph",
    f"{PACKAGE_ROOT}.semantic.node",
    f"{PACKAGE_ROOT}.semantic.pin",
    f"{PACKAGE_ROOT}.semantic.connection",
)


@pytest.mark.parametrize("module", DELETED_SEMANTIC_TOPOLOGY_MODULES)
def test_deleted_semantic_topology_modules_stay_dead(module: str) -> None:
    """No file in src/ may import ``semantic.<topology shim>`` again."""
    violations: list[str] = []
    for py_file in _iter_python_files(SRC_ROOT):
        rel = py_file.relative_to(SRC_ROOT)
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_file))
        for imported in _collect_imported_modules(tree):
            if imported == module or imported.startswith(f"{module}."):
                violations.append(f"{rel}: imports {imported}")
    assert not violations, (
        f"{module} is a deleted shim; topology lives in core. Violations:\n" + "\n".join(violations)
    )


def test_animation_does_not_import_renderer_private_symbols() -> None:
    animation_dir = SRC_ROOT / "animation"
    violations: list[str] = []
    for py_file in _iter_python_files(animation_dir):
        rel = py_file.relative_to(SRC_ROOT)
        source = py_file.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(py_file))
        for imported in _collect_imported_modules(tree):
            if "renderers" not in imported:
                continue
            for name in ("_point3", "_trace_color"):
                if f".{name}" in imported or imported.endswith(name):
                    violations.append(f"{rel}: imports {imported}")
    assert not violations, "Animation must use public renderer helpers:\n" + "\n".join(violations)
