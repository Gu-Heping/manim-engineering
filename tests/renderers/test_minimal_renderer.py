"""MinimalRenderer structure and determinism tests."""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("manim")

from manim_engineering.components import Resistor
from manim_engineering.core import CircuitGraph
from manim_engineering.layout import LayoutEngine
from manim_engineering.renderers.minimal import MinimalRenderer


def _two_resistor_graph() -> tuple[CircuitGraph, Resistor, Resistor]:
    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r2 = Resistor("r2", label="R2")
    r1.attach_to(graph)
    r2.attach_to(graph)
    graph.connect(r1.get_pin("b"), r2.get_pin("a"))
    return graph, r1, r2


def test_minimal_renderer_module_importable() -> None:
    assert MinimalRenderer is not None


def test_render_resistor_deterministic_structure() -> None:
    renderer = MinimalRenderer()
    r1 = Resistor("r1", label="R1")
    first = renderer.render(r1)
    second = renderer.render(r1)

    assert len(first.submobjects) == len(second.submobjects)
    assert np.allclose(first.get_all_points(), second.get_all_points())


def test_render_resistor_has_body_and_label() -> None:
    mob = MinimalRenderer().render(Resistor("r1", label="R1"))
    assert len(mob.submobjects) == 3  # body, pin dots, label


def test_component_label_font_size_uses_point_scale() -> None:
    from manim_engineering.renderers.minimal import theme

    assert isinstance(theme.COMPONENT_LABEL_FONT_SIZE, int)
    assert theme.COMPONENT_LABEL_FONT_SIZE >= 16


def test_resistor_label_world_height_readable() -> None:
    """Regression: microscopic font_size (e.g. 0.18 pt) yields near-zero height."""
    mob = MinimalRenderer().render(Resistor("r1", label="R1"))
    label = mob.submobjects[-1]
    assert label.height > 0.12


def test_render_layout_includes_components_and_wires() -> None:
    graph, r1, r2 = _two_resistor_graph()
    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().layout(graph, elements)
    scene = MinimalRenderer().render_layout(layout, graph, elements)

    # Two resistor groups (body+label each) + wire segments
    assert len(scene.submobjects) >= 3


def test_render_layout_separates_placed_components() -> None:
    from manim_engineering.components import Capacitor

    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    c1 = Capacitor("c1", label="C1")
    graph.add(r1)
    graph.add(c1)
    graph.connect(r1.port_b, c1.port_a)

    elements = {"r1": r1, "c1": c1}
    layout = LayoutEngine().solve(graph, elements)
    scene = MinimalRenderer().render_layout(layout, graph, elements)

    by_id = {p.element_id: scene.submobjects[i] for i, p in enumerate(layout.placements)}
    c1_x = by_id["c1"].get_all_points()[:, 0]
    r1_x = by_id["r1"].get_all_points()[:, 0]
    assert float(r1_x.max()) < float(c1_x.min()) - 0.1


def test_render_layout_deterministic_points() -> None:
    graph, r1, r2 = _two_resistor_graph()
    elements = {"r1": r1, "r2": r2}
    layout = LayoutEngine().layout(graph, elements)
    renderer = MinimalRenderer()
    first = renderer.render_layout(layout, graph, elements)
    second = renderer.render_layout(layout, graph, elements)
    assert np.allclose(first.get_all_points(), second.get_all_points())


def _analog_render_smoke(component) -> None:
    """Shared analog symbol contract: VGroup, body subgroup non-empty,
    deterministic submobject count across repeated renders."""
    renderer = MinimalRenderer()
    first = renderer.render(component)
    second = renderer.render(component)
    assert len(first.submobjects) > 0
    assert len(first.submobjects) == len(second.submobjects)
    # Body subgroup (first child) must contain at least 1 stroke primitive.
    body = first.submobjects[0]
    assert len(body.submobjects) > 0


def test_renders_nmos_symbol_returns_vgroup() -> None:
    from manim_engineering.components import NMOS

    _analog_render_smoke(NMOS("m1", label="M1"))


def test_renders_pmos_symbol_returns_vgroup() -> None:
    from manim_engineering.components import PMOS

    _analog_render_smoke(PMOS("p1", label="P1"))


def test_renders_diode_symbol_returns_vgroup() -> None:
    from manim_engineering.components import Diode

    _analog_render_smoke(Diode("d1", label="D1"))


def test_renders_op_amp_symbol_returns_vgroup() -> None:
    from manim_engineering.components import OpAmp

    _analog_render_smoke(OpAmp("u1", label="U1"))


def test_renders_input_driver_symbol_returns_vgroup() -> None:
    from manim_engineering.components import InputDriver

    _analog_render_smoke(InputDriver("in1", label="IN"))


def test_input_driver_symbol_label_renders() -> None:
    """Body wedge + label text (no pin dots for io markers)."""
    from manim_engineering.components import InputDriver

    mob = MinimalRenderer().render(InputDriver("in1", label="IN"))
    assert len(mob.submobjects) == 2


def _body_endpoint_coords(body) -> set[tuple[float, float]]:
    """Collect all polyline vertex coordinates from a symbol body VGroup."""
    coords: set[tuple[float, float]] = set()
    for sub in body.submobjects:
        pts = sub.get_all_points()
        for pt in pts:
            coords.add((round(float(pt[0]), 4), round(float(pt[1]), 4)))
    return coords


def test_vcc_and_ground_labels_clear_of_symbol_body() -> None:
    from manim_engineering.components import VCC, Ground

    vcc = VCC("vcc1", label="VCC")
    gnd = Ground("gnd1", label="GND")
    vcc_mob = MinimalRenderer().render(vcc)
    gnd_mob = MinimalRenderer().render(gnd)
    vcc_label = vcc_mob.submobjects[-1]
    gnd_label = gnd_mob.submobjects[-1]
    _, vh = vcc.get_bounds().width, vcc.get_bounds().height
    _, _gh = gnd.get_bounds().width, gnd.get_bounds().height

    assert float(vcc_label.get_center()[1]) > vh
    assert float(gnd_label.get_center()[1]) < 0.0


def test_vcc_symbol_stroke_meets_bottom_anchor() -> None:
    from manim_engineering.components import VCC

    vcc = VCC("vcc1")
    body = MinimalRenderer().render(vcc).submobjects[0]
    w, _h = vcc.get_bounds().width, vcc.get_bounds().height
    cx = w * 0.5
    coords = _body_endpoint_coords(body)
    assert (round(cx, 4), 0.0) in coords


def test_pmos_symbol_strokes_end_at_source_and_drain_anchors() -> None:
    from manim_engineering.components import PMOS
    from manim_engineering.components.analog.mosfet import (
        MOSFET_DRAIN_STUB_X,
        MOSFET_SOURCE_STUB_X,
    )

    pmos = PMOS("p1")
    body = MinimalRenderer().render(pmos).submobjects[0]
    w, h = pmos.get_bounds().width, pmos.get_bounds().height
    coords = _body_endpoint_coords(body)
    drain_x = round(MOSFET_DRAIN_STUB_X * w, 4)
    source_x = round(MOSFET_SOURCE_STUB_X * w, 4)
    assert (drain_x, 0.0) in coords
    assert (source_x, round(h, 4)) in coords


def _all_text_submobjects(mob) -> list:
    from manim import Text

    found: list = []
    for sub in mob.submobjects:
        if isinstance(sub, Text):
            found.append(sub)
        elif hasattr(sub, "submobjects"):
            found.extend(_all_text_submobjects(sub))
    return found


def test_spi_master_pin_labels_outside_body() -> None:
    from manim_engineering.components import SPIMaster

    master = SPIMaster("mcu", label="MCU")
    w, _h = master.get_bounds().width, master.get_bounds().height
    mob = MinimalRenderer().render(master)
    pin_texts = [t for t in _all_text_submobjects(mob) if t.text in master.pins]
    assert len(pin_texts) == 4  # clk, mosi, cs left + miso right (slave skips miso)
    for label in pin_texts:
        cx = float(label.get_center()[0])
        if label.text in ("clk", "mosi", "cs"):
            assert cx < 0.0, f"{label.text} center should be left of body (cx={cx})"
        elif label.text == "miso":
            assert cx > w, f"miso should be right of body (cx={cx}, w={w})"


def test_spi_slave_skips_miso_pin_label() -> None:
    from manim_engineering.components import SPISlave

    mob = MinimalRenderer().render(SPISlave("slv"))
    pin_texts = [t.text for t in _all_text_submobjects(mob) if t.text in SPISlave("x").pins]
    assert "miso" not in pin_texts
    assert set(pin_texts) == {"clk", "mosi", "cs"}


def test_uart_port_pin_labels_outside_body() -> None:
    from manim_engineering.components import UARTPort

    port = UARTPort("host", label="HOST")
    mob = MinimalRenderer().render(port)
    pin_texts = [t for t in _all_text_submobjects(mob) if t.text in port.pins]
    for label in pin_texts:
        if label.text in ("tx", "rx"):
            assert float(label.get_center()[0]) < 0.0
        elif label.text == "gnd":
            assert float(label.get_center()[1]) < 0.0


def test_uart_role_glyph_is_single_letter() -> None:
    from manim_engineering.components import UARTPort

    mob = MinimalRenderer().render(UARTPort("u1"))
    role_texts = [t.text for t in _all_text_submobjects(mob) if t.text in ("U", "UART")]
    assert role_texts == ["U"]


def test_spi_master_uses_hollow_interface_outline() -> None:
    from manim import Line, Rectangle, VGroup

    from manim_engineering.components import SPIMaster
    from manim_engineering.renderers.minimal import theme

    mob = MinimalRenderer().render(SPIMaster("mcu"))
    body = mob.submobjects[0]
    assert isinstance(body.submobjects[0], Rectangle)
    assert str(body.submobjects[0].get_fill_color()).lower() == theme.INTERFACE_PANEL_FILL.lower()
    outline = body.submobjects[1]
    assert isinstance(outline, VGroup)
    assert len(outline.submobjects) == 4
    assert all(isinstance(edge, Line) for edge in outline.submobjects)
    assert outline.submobjects[0].get_stroke_width() == theme.interface_box_stroke_width()
    assert (
        str(outline.submobjects[0].get_stroke_color()).lower()
        == str(theme.interface_box_stroke_color()).lower()
    )


def test_spi_master_no_pin_label_inside_box_interior() -> None:
    from manim_engineering.components import SPIMaster

    master = SPIMaster("mcu")
    w, h = master.get_bounds().width, master.get_bounds().height
    mob = MinimalRenderer().render(master)
    for label in _all_text_submobjects(mob):
        if label.text not in master.pins:
            continue
        cx, cy = float(label.get_center()[0]), float(label.get_center()[1])
        inside = 0.0 < cx < w and 0.0 < cy < h
        assert not inside, f"{label.text} at ({cx},{cy}) inside box interior"


def test_interface_labeled_pins_skip_direction_stubs() -> None:
    """Short direction ticks beside pin names read as glyph halos on dark frames."""
    from manim import Line

    from manim_engineering.components import SPIMaster

    master = SPIMaster("mcu")
    mob = MinimalRenderer().render(master)
    body = mob.submobjects[0]
    short_lines = [
        sub for sub in body.submobjects if isinstance(sub, Line) and sub.get_length() < 0.2
    ]
    assert not short_lines


def test_stroke_only_refresh_preserves_dimmed_fill() -> None:
    from manim import VGroup

    from manim_engineering.renderers.minimal.labels import label_text, refresh_label_strokes

    label = label_text("cs", font_size=12, color="#58C4DD")
    group = VGroup(label)
    group.set_opacity(0.35)
    refresh_label_strokes(group, mode="stroke_only")
    for sub in label.get_family():
        if len(sub.points) == 0:
            continue
        assert sub.get_stroke_opacity() == 0.0
        assert float(sub.get_fill_opacity()) == pytest.approx(0.35, abs=0.05)


def test_refresh_label_strokes_fixes_glyphs_under_partial_opacity() -> None:
    from manim import VGroup

    from manim_engineering.renderers.minimal.labels import label_text, refresh_label_strokes

    label = label_text("cs", font_size=12, color="#58C4DD")
    group = VGroup(label)
    group.set_opacity(0.35)
    refresh_label_strokes(group, mode="full")
    for sub in label.get_family():
        if len(sub.points) == 0:
            continue
        assert sub.get_stroke_opacity() == 0.0
        assert sub.get_stroke_rgbas()[0, 3] == 0.0
        assert str(sub.get_fill_color()).lower() != "#ffffff"


def test_fade_in_opacity_on_components_then_normalize_fixes_pin_labels() -> None:
    """Intro ``FadeIn(topology.components)`` leaves white glyph strokes until refreshed."""
    from manim_engineering.animation.focus import normalize_topology_labels
    from manim_engineering.components import SPIMaster, SPISlave
    from manim_engineering.core import CircuitGraph
    from manim_engineering.layout import LayoutConfig, LayoutEngine
    from manim_engineering.renderers.minimal import ManimRenderer

    graph = CircuitGraph()
    master = SPIMaster("master")
    slave = SPISlave("slave")
    master.attach_to(graph)
    slave.attach_to(graph)
    elements = {"master": master, "slave": slave}
    layout = LayoutEngine(LayoutConfig(cell_gap=0.85)).layout(graph, elements)
    topology = ManimRenderer().render_topology(graph, layout, elements)
    topology.components.set_opacity(0.0)
    topology.components.set_opacity(1.0)
    normalize_topology_labels(topology)
    topo_pins = [t for t in _all_text_submobjects(topology.components) if t.text in master.pins]
    assert topo_pins
    for label in topo_pins:
        for sub in label.get_family():
            if len(sub.points) == 0:
                continue
            assert sub.get_stroke_opacity() == 0.0
            assert str(sub.get_fill_color()).lower() != "#ffffff"


def test_refresh_label_strokes_preserves_component_line_stroke_width() -> None:
    """Empty VGroup containers must not cascade stroke width=0 onto symbol Lines."""
    from manim_engineering.components import Capacitor, Resistor
    from manim_engineering.core import CircuitGraph
    from manim_engineering.layout import LayoutEngine
    from manim_engineering.renderers.minimal import ManimRenderer
    from manim_engineering.renderers.minimal.labels import refresh_label_strokes

    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    c1 = Capacitor("c1", label="C1")
    r1.attach_to(graph)
    c1.attach_to(graph)
    graph.connect(r1.get_pin("b"), c1.get_pin("a"))
    layout = LayoutEngine().layout(graph, {"r1": r1, "c1": c1})
    topology = ManimRenderer().render_topology(graph, layout, {"r1": r1, "c1": c1})
    lines = [
        mob
        for mob in topology.components.get_family()
        if mob.__class__.__name__ == "Line" and len(mob.points) > 0
    ]
    assert lines
    widths_before = [mob.get_stroke_width() for mob in lines]
    assert all(width > 0 for width in widths_before)
    refresh_label_strokes(topology.components, mode="full")
    for mob, width_before in zip(lines, widths_before, strict=True):
        assert mob.get_stroke_width() == pytest.approx(width_before)


def test_set_opacity_restore_does_not_fill_resistor_lines() -> None:
    from manim_engineering.animation.focus import normalize_topology_labels
    from manim_engineering.components import Resistor
    from manim_engineering.core import CircuitGraph
    from manim_engineering.layout import LayoutEngine
    from manim_engineering.renderers.minimal import ManimRenderer

    graph = CircuitGraph()
    r1 = Resistor("r1", label="R1")
    r1.attach_to(graph)
    layout = LayoutEngine().layout(graph, {"r1": r1})
    topology = ManimRenderer().render_topology(graph, layout, {"r1": r1})
    lines = [
        mob
        for mob in topology.components.get_family()
        if mob.__class__.__name__ == "Line" and len(mob.points) > 0
    ]
    assert lines
    assert all(mob.get_fill_opacity() == 0.0 for mob in lines)
    topology.components.set_opacity(1.0)
    assert all(mob.get_fill_opacity() == 1.0 for mob in lines)
    normalize_topology_labels(topology)
    assert all(mob.get_fill_opacity() == 0.0 for mob in lines)
    assert all(mob.get_stroke_width() > 0 for mob in lines)


def test_dim_topology_keeps_pin_labels_at_dim_opacity() -> None:
    """stroke_only refresh must not pop label fill back to 1.0 while dimmed."""
    from manim_engineering.animation.focus import DEFAULT_DIM_OPACITY, dim_topology
    from manim_engineering.components import SPIMaster, SPISlave
    from manim_engineering.core import CircuitGraph
    from manim_engineering.layout import LayoutConfig, LayoutEngine
    from manim_engineering.renderers.minimal import ManimRenderer

    graph = CircuitGraph()
    master = SPIMaster("master")
    slave = SPISlave("slave")
    master.attach_to(graph)
    slave.attach_to(graph)
    elements = {"master": master, "slave": slave}
    layout = LayoutEngine(LayoutConfig(cell_gap=0.85)).layout(graph, elements)
    topology = ManimRenderer().render_topology(graph, layout, elements)
    dim_topology(topology)
    topo_pins = [t for t in _all_text_submobjects(topology.components) if t.text in master.pins]
    assert topo_pins
    for label in topo_pins:
        for sub in label.get_family():
            if len(sub.points) == 0:
                continue
            fill_alpha = float(sub.get_fill_opacity())
            assert fill_alpha == pytest.approx(DEFAULT_DIM_OPACITY, abs=0.05)
            assert sub.get_stroke_opacity() == 0.0


def test_dim_restore_topology_keeps_pin_labels_without_stroke() -> None:
    from manim_engineering.animation.focus import dim_topology, restore_topology
    from manim_engineering.components import SPIMaster, SPISlave
    from manim_engineering.core import CircuitGraph
    from manim_engineering.layout import LayoutConfig, LayoutEngine
    from manim_engineering.renderers.minimal import ManimRenderer

    graph = CircuitGraph()
    master = SPIMaster("master")
    slave = SPISlave("slave")
    master.attach_to(graph)
    slave.attach_to(graph)
    elements = {"master": master, "slave": slave}
    layout = LayoutEngine(LayoutConfig(cell_gap=0.85)).layout(graph, elements)
    topology = ManimRenderer().render_topology(graph, layout, elements)
    dim_topology(topology)
    restore_topology(topology)
    topo_pins = [t for t in _all_text_submobjects(topology.components) if t.text in master.pins]
    assert topo_pins
    for label in topo_pins:
        for sub in label.get_family():
            if len(sub.points) == 0:
                continue
            assert sub.get_stroke_opacity() == 0.0
            assert sub.get_stroke_rgbas()[0, 3] == 0.0
            assert str(sub.get_fill_color()).lower() != "#ffffff"


def test_interface_pin_labels_have_no_text_stroke() -> None:
    from manim_engineering.components import SPIMaster
    from manim_engineering.renderers.minimal.labels import LABEL_Z_INDEX

    mob = MinimalRenderer().render(SPIMaster("mcu"))
    pin_texts = [
        t
        for t in _all_text_submobjects(mob)
        if t.text in SPIMaster("x").pins  # same pin names
    ]
    assert pin_texts
    for label in pin_texts:
        assert label.get_stroke_width() == 0.0
        assert label.get_stroke_opacity() == 0.0
        glyph_subs = [s for s in label.get_family() if len(s.points) > 0]
        assert glyph_subs
        for sub in glyph_subs:
            assert sub.get_z_index() == LABEL_Z_INDEX
            assert sub.get_stroke_width() == 0.0
            assert sub.get_stroke_opacity() == 0.0


def test_spi_master_mcu_label_clear_of_pin_labels() -> None:
    from manim_engineering.components import SPIMaster

    master = SPIMaster("mcu", label="MCU")
    mob = MinimalRenderer().render(master)
    mcu = next(t for t in _all_text_submobjects(mob) if t.text == "MCU")
    pin_labels = [t for t in _all_text_submobjects(mob) if t.text in master.pins]
    assert pin_labels
    highest_pin_top = max(float(t.get_top()[1]) for t in pin_labels)
    mcu_bottom = float(mcu.get_bottom()[1])
    assert mcu_bottom - highest_pin_top >= 0.05, (
        f"MCU label should clear pin labels (gap={mcu_bottom - highest_pin_top:.3f})"
    )


def test_interface_skips_pin_dots() -> None:
    from manim import Dot

    from manim_engineering.components import SPIMaster

    mob = MinimalRenderer().render(SPIMaster("mcu", label="MCU"))
    assert not any(isinstance(s, Dot) for s in mob.submobjects)


def test_nmos_symbol_strokes_end_at_drain_and_source_anchors() -> None:
    from manim_engineering.components import NMOS
    from manim_engineering.components.analog.mosfet import (
        MOSFET_DRAIN_STUB_X,
        MOSFET_SOURCE_STUB_X,
    )

    nmos = NMOS("m1")
    body = MinimalRenderer().render(nmos).submobjects[0]
    w, h = nmos.get_bounds().width, nmos.get_bounds().height
    coords = _body_endpoint_coords(body)
    drain_x = round(MOSFET_DRAIN_STUB_X * w, 4)
    source_x = round(MOSFET_SOURCE_STUB_X * w, 4)
    assert (drain_x, round(h, 4)) in coords
    assert (source_x, 0.0) in coords
