from __future__ import annotations

import pytest

pytest.importorskip("manim")

import manim_engineering.quickstart as quickstart_module
from manim_engineering import build_circuit, layout_circuit, render_circuit_diagram
from manim_engineering.components import CurrentProbe, Ground, Resistor, VoltageProbe


def test_render_circuit_diagram_returns_rendered_group_and_topology() -> None:
    build = build_circuit(
        {
            "r1": Resistor("r1", label="R1"),
            "r2": Resistor("r2", label="R2"),
        },
        [("r1", "b", "r2", "a")],
    )
    layout = layout_circuit(build)

    result = render_circuit_diagram(build, layout)

    assert len(result.rendered.submobjects) >= 3
    assert result.topology is not None
    assert result.topology.n_components == 2
    assert result.output_path is None
    assert result.preview_attempted is False
    assert result.preview_available is False
    assert result.warnings == ()


def test_render_circuit_diagram_handles_measurement_probe_circuit() -> None:
    build = build_circuit(
        {
            "ip": CurrentProbe("ip", label="I"),
            "load": Resistor("load", label="Rload"),
            "vp": VoltageProbe("vp", label="Vload"),
            "gnd": Ground("gnd", label="GND"),
        },
        [
            ("ip", "out", "load", "a"),
            ("load", "b", "gnd", "gnd"),
            ("vp", "pos", "load", "b"),
            ("vp", "neg", "gnd", "gnd"),
        ],
    )
    layout = layout_circuit(build)

    result = render_circuit_diagram(build, layout)

    assert result.topology is not None
    assert result.topology.n_components == 4
    assert [mob.element_id for mob in result.topology.components.submobjects] == [
        placement.element_id for placement in layout.layout.placements
    ]
    assert result.output_path is None


def test_render_circuit_diagram_exports_png_preview(tmp_path) -> None:
    build = build_circuit(
        {
            "r1": Resistor("r1"),
            "r2": Resistor("r2"),
        },
        [("r1", "b", "r2", "a")],
    )
    layout = layout_circuit(build)

    result = render_circuit_diagram(
        build,
        layout,
        include_topology=False,
        output_path=tmp_path / "preview.png",
    )

    assert result.topology is None
    assert result.output_path == tmp_path / "preview.png"
    assert result.output_path.exists()
    assert result.preview_attempted is False
    assert result.preview_available is False
    assert result.warnings == ()


def test_render_circuit_diagram_attempts_preview_open_when_supported(monkeypatch, tmp_path) -> None:
    build = build_circuit(
        {
            "r1": Resistor("r1"),
            "r2": Resistor("r2"),
        },
        [("r1", "b", "r2", "a")],
    )
    layout = layout_circuit(build)

    opened: list[str] = []
    monkeypatch.setattr(
        quickstart_module.os,
        "startfile",
        lambda path: opened.append(path),
        raising=False,
    )

    result = render_circuit_diagram(
        build,
        layout,
        include_topology=False,
        output_path=tmp_path / "preview.png",
        preview=True,
    )

    assert opened == [str(tmp_path / "preview.png")]
    assert result.preview_attempted is True
    assert result.preview_available is True
    assert result.output_path == tmp_path / "preview.png"


def test_render_circuit_diagram_handles_preview_open_failure(monkeypatch, tmp_path) -> None:
    build = build_circuit(
        {
            "r1": Resistor("r1"),
            "r2": Resistor("r2"),
        },
        [("r1", "b", "r2", "a")],
    )
    layout = layout_circuit(build)

    def _fail_startfile(path: str) -> None:
        raise OSError(f"cannot open {path}")

    monkeypatch.setattr(
        quickstart_module.os,
        "startfile",
        _fail_startfile,
        raising=False,
    )

    result = render_circuit_diagram(
        build,
        layout,
        include_topology=False,
        output_path=tmp_path / "preview.png",
        preview=True,
    )

    assert result.preview_attempted is True
    assert result.preview_available is False
    assert "preview.open_unavailable" in result.warnings


def test_render_circuit_diagram_preview_requires_output_path() -> None:
    build = build_circuit(
        {
            "r1": Resistor("r1"),
            "r2": Resistor("r2"),
        },
        [("r1", "b", "r2", "a")],
    )
    layout = layout_circuit(build)

    result = render_circuit_diagram(build, layout, preview=True, include_topology=False)

    assert result.output_path is None
    assert result.preview_attempted is True
    assert result.preview_available is False
    assert "preview.requires_output_path" in result.warnings
