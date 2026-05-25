"""MOSFET four-type and symbol-convention renderer tests."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim import Circle, Dot, Line, VGroup

from manim_engineering.components import NMOS, NMOSDepletion, PMOS, PMOSDepletion
from manim_engineering.components.analog.mosfet import (
    MOSFET_CHANNEL_X,
    MOSFET_DRAIN_STUB_X,
    MOSFET_SOURCE_STUB_X,
)
from manim_engineering.renderers.minimal import MinimalRenderer, MosfetSymbolConvention


def _body_endpoint_coords(body) -> set[tuple[float, float]]:
    coords: set[tuple[float, float]] = set()
    for sub in body.submobjects:
        for pt in sub.get_all_points():
            coords.add((round(float(pt[0]), 4), round(float(pt[1]), 4)))
    return coords


def _vertical_channel_lines(body, channel_x: float) -> list[Line]:
    lines: list[Line] = []
    for sub in body.submobjects:
        if not isinstance(sub, Line):
            continue
        x0 = round(float(sub.get_start()[0]), 4)
        x1 = round(float(sub.get_end()[0]), 4)
        if x0 != round(channel_x, 4) or x1 != round(channel_x, 4):
            continue
        lines.append(sub)
    return lines


def _vertical_lines_at_x(body, x: float) -> list[Line]:
    target = round(x, 4)
    lines: list[Line] = []
    for sub in body.submobjects:
        if not isinstance(sub, Line):
            continue
        x0 = round(float(sub.get_start()[0]), 4)
        x1 = round(float(sub.get_end()[0]), 4)
        if x0 == target and x1 == target:
            lines.append(sub)
    return lines


@pytest.mark.parametrize(
    "factory",
    [
        lambda: NMOS("n1"),
        lambda: PMOS("p1"),
        lambda: NMOSDepletion("nd1"),
        lambda: PMOSDepletion("pd1"),
    ],
)
def test_textbook_vertical_anchors_at_stub_columns(factory) -> None:
    component = factory()
    body = MinimalRenderer().render(component).submobjects[0]
    w, h = component.get_bounds().width, component.get_bounds().height
    coords = _body_endpoint_coords(body)
    drain_x = round(MOSFET_DRAIN_STUB_X * w, 4)
    source_x = round(MOSFET_SOURCE_STUB_X * w, 4)
    assert (0.0, round(0.5 * h, 4)) in coords
    assert (drain_x, round(h, 4)) in coords or (drain_x, 0.0) in coords
    assert (source_x, round(h, 4)) in coords or (source_x, 0.0) in coords


@pytest.mark.parametrize(
    "factory",
    [
        lambda: NMOS("n1"),
        lambda: PMOS("p1"),
        lambda: NMOSDepletion("nd1"),
        lambda: PMOSDepletion("pd1"),
    ],
)
@pytest.mark.parametrize(
    "convention",
    [
        MosfetSymbolConvention.ieee_simplified,
        MosfetSymbolConvention.arrow_on_channel,
    ],
)
def test_legacy_adds_horizontal_stub_endpoints(factory, convention) -> None:
    component = factory()
    body = MinimalRenderer(mosfet_convention=convention).render(component).submobjects[0]
    w, h = component.get_bounds().width, component.get_bounds().height
    coords = _body_endpoint_coords(body)
    drain_x = round(MOSFET_DRAIN_STUB_X * w, 4)
    source_x = round(MOSFET_SOURCE_STUB_X * w, 4)
    assert (drain_x, round(h, 4)) in coords or (drain_x, 0.0) in coords
    assert (source_x, round(h, 4)) in coords or (source_x, 0.0) in coords


def test_textbook_enhancement_stub_columns_separated() -> None:
    nmos = NMOS("n1")
    body = MinimalRenderer().render(nmos).submobjects[0]
    w = nmos.get_bounds().width
    drain_x = MOSFET_DRAIN_STUB_X * w
    source_x = MOSFET_SOURCE_STUB_X * w
    drain_verticals = _vertical_lines_at_x(body, drain_x)
    source_verticals = _vertical_lines_at_x(body, source_x)
    assert drain_verticals
    assert source_verticals
    assert drain_x != pytest.approx(source_x)


@pytest.mark.parametrize(
    ("factory", "expect_three_channel_bars"),
    [
        (lambda: NMOS("n1"), True),
        (lambda: PMOS("p1"), True),
        (lambda: NMOSDepletion("nd1"), False),
        (lambda: PMOSDepletion("pd1"), False),
    ],
)
def test_enhancement_three_channel_bars_vs_depletion_solid(
    factory,
    expect_three_channel_bars,
) -> None:
    component = factory()
    body = MinimalRenderer().render(component).submobjects[0]
    w = component.get_bounds().width
    channel_x = MOSFET_CHANNEL_X * w
    channel_lines = _vertical_channel_lines(body, channel_x)
    if expect_three_channel_bars:
        assert len(channel_lines) == 3
        lengths = sorted(abs(float(line.get_end()[1] - line.get_start()[1])) for line in channel_lines)
        assert lengths[0] == pytest.approx(lengths[1], rel=0.05)
        assert lengths[1] == pytest.approx(lengths[2], rel=0.05)
    else:
        assert len(channel_lines) == 1


def test_textbook_enhancement_uses_three_discrete_channel_bars() -> None:
    nmos = NMOS("n1")
    body = MinimalRenderer().render(nmos).submobjects[0]
    channel_x = MOSFET_CHANNEL_X * nmos.get_bounds().width
    assert len(_vertical_channel_lines(body, channel_x)) == 3


def test_textbook_mosfet_pin_dots_exclude_bulk_only() -> None:
    for factory in (NMOS, PMOS):
        component = factory("m")
        w, h = component.get_bounds().width, component.get_bounds().height
        mob = MinimalRenderer().render(component)
        dot_coords = {
            (round(float(sub.get_center()[0]), 4), round(float(sub.get_center()[1]), 4))
            for group in mob.submobjects
            if isinstance(group, VGroup)
            for sub in group.submobjects
            if isinstance(sub, Dot)
        }
        assert (0.0, round(0.5 * h, 4)) in dot_coords
        bulk_y = round(component.anchor_points["bulk"][1] * h, 4)
        assert (round(MOSFET_SOURCE_STUB_X * w, 4), bulk_y) not in dot_coords


def test_pmos_gate_lead_has_no_inversion_bubble() -> None:
    body = MinimalRenderer().render(PMOS("p1")).submobjects[0]
    assert not any(isinstance(sub, Circle) for sub in body.submobjects)


def test_textbook_bulk_stub_meets_source_branch_without_junction_dot() -> None:
    nmos = NMOS("n1")
    body = MinimalRenderer().render(nmos).submobjects[0]
    assert not any(isinstance(sub, Dot) for sub in body.submobjects)
    stub_x = MOSFET_SOURCE_STUB_X * nmos.get_bounds().width
    bulk_stub_lines = [
        sub
        for sub in body.submobjects
        if isinstance(sub, Line)
        and round(float(sub.get_start()[0]), 4) == round(stub_x, 4)
        and round(float(sub.get_end()[0]), 4) == round(stub_x, 4)
    ]
    assert bulk_stub_lines


def test_mosfet_label_sits_left_of_gate() -> None:
    nmos = NMOS("n1", label="NMOS")
    mob = MinimalRenderer().render(nmos)
    label = mob.submobjects[-1]
    assert float(label.get_center()[0]) < 0.0
    assert float(label.get_center()[1]) == pytest.approx(0.5, abs=0.15)


def test_depletion_components_metadata() -> None:
    assert NMOSDepletion.conduction_mode == "depletion"
    assert PMOSDepletion.conduction_mode == "depletion"
    assert NMOS.conduction_mode == "enhancement"
    assert PMOS.conduction_mode == "enhancement"
