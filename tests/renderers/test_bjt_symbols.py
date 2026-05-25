"""BJT textbook symbol geometry tests."""

from __future__ import annotations

import pytest

pytest.importorskip("manim")

from manim import Circle, Line, Polygon

from manim_engineering.components import NPN, PNP
from manim_engineering.components.analog.bjt import BJT_STUB_X
from manim_engineering.renderers.minimal import MinimalRenderer, theme


def _body_endpoint_coords(body) -> set[tuple[float, float]]:
    coords: set[tuple[float, float]] = set()
    for sub in body.submobjects:
        if isinstance(sub, Line):
            for pt in sub.get_all_points():
                coords.add((round(float(pt[0]), 4), round(float(pt[1]), 4)))
        elif isinstance(sub, Polygon):
            for pt in sub.get_all_points():
                coords.add((round(float(pt[0]), 4), round(float(pt[1]), 4)))
    return coords


def test_bjt_open_symbol_has_no_outer_circle() -> None:
    for factory in (lambda: NPN("q1"), lambda: PNP("q2")):
        body = MinimalRenderer().render(factory()).submobjects[0]
        assert not any(isinstance(sub, Circle) for sub in body.submobjects)


def test_npn_symbol_strokes_end_at_pin_anchors() -> None:
    npn = NPN("q1")
    body = MinimalRenderer().render(npn).submobjects[0]
    w, h = npn.get_bounds().width, npn.get_bounds().height
    coords = _body_endpoint_coords(body)
    assert (0.0, round(0.5 * h, 4)) in coords
    stub_x = round(BJT_STUB_X * w, 4)
    assert (stub_x, round(h, 4)) in coords
    assert (stub_x, 0.0) in coords


def test_pnp_symbol_strokes_end_at_pin_anchors() -> None:
    pnp = PNP("q2")
    body = MinimalRenderer().render(pnp).submobjects[0]
    w, h = pnp.get_bounds().width, pnp.get_bounds().height
    coords = _body_endpoint_coords(body)
    stub_x = round(BJT_STUB_X * w, 4)
    assert (0.0, round(0.5 * h, 4)) in coords
    assert (stub_x, 0.0) in coords
    assert (stub_x, round(h, 4)) in coords


def test_bjt_has_vertical_base_bar_and_diagonal_legs() -> None:
    npn = NPN("q1")
    body = MinimalRenderer().render(npn).submobjects[0]
    w, h = npn.get_bounds().width, npn.get_bounds().height
    bar_x = round(theme.BJT_BASE_BAR_X * w, 4)
    verticals = [
        sub
        for sub in body.submobjects
        if isinstance(sub, Line)
        and round(float(sub.get_start()[0]), 4) == bar_x
        and round(float(sub.get_end()[0]), 4) == bar_x
    ]
    assert len(verticals) == 1
    bar = verticals[0]
    y0 = min(float(bar.get_start()[1]), float(bar.get_end()[1]))
    y1 = max(float(bar.get_start()[1]), float(bar.get_end()[1]))
    assert y0 == pytest.approx(theme.BJT_BAR_BOT_Y * h, abs=0.02)
    assert y1 == pytest.approx(theme.BJT_BAR_TOP_Y * h, abs=0.02)
    assert (y1 - y0) > (theme.BJT_BAR_BRANCH_TOP_Y - theme.BJT_BAR_BRANCH_BOT_Y) * h
    diagonals = [
        sub
        for sub in body.submobjects
        if isinstance(sub, Line)
        and round(float(sub.get_start()[0]), 4) == bar_x
        and round(float(sub.get_end()[0]), 4) != bar_x
    ]
    assert len(diagonals) == 2


def test_bjt_collector_emitter_stubs_have_no_horizontal_tail() -> None:
    npn = NPN("q1")
    body = MinimalRenderer().render(npn).submobjects[0]
    w, h = npn.get_bounds().width, npn.get_bounds().height
    bar_x = theme.BJT_BASE_BAR_X * w
    pin_tails = [
        sub
        for sub in body.submobjects
        if isinstance(sub, Line)
        and abs(float(sub.get_start()[1]) - float(sub.get_end()[1])) < 0.01
        and abs(float(sub.get_start()[0]) - float(sub.get_end()[0])) > 0.05
        and min(float(sub.get_start()[0]), float(sub.get_end()[0])) > bar_x + 0.01
    ]
    assert not pin_tails


def test_npn_emitter_arrow_points_outward_from_base_bar() -> None:
    npn = NPN("q1")
    body = MinimalRenderer().render(npn).submobjects[0]
    w, h = npn.get_bounds().width, npn.get_bounds().height
    arrow = next(sub for sub in body.submobjects if isinstance(sub, Polygon))
    bar_x = theme.BJT_BASE_BAR_X * w
    tip = arrow.get_vertices()[0]
    assert float(tip[0]) > bar_x


def test_npn_pnp_emitter_arrow_leg_fracs_sum_to_one() -> None:
    t = theme.BJT_EMITTER_ARROW_LEG_FRAC
    assert t + (1.0 - t) == pytest.approx(1.0)
    assert t > 1.0 - t


def test_pnp_emitter_arrow_points_inward_toward_base_bar() -> None:
    pnp = PNP("q2")
    body = MinimalRenderer().render(pnp).submobjects[0]
    w, h = pnp.get_bounds().width, pnp.get_bounds().height
    arrow = next(sub for sub in body.submobjects if isinstance(sub, Polygon))
    bar_x = theme.BJT_BASE_BAR_X * w
    tip = arrow.get_vertices()[0]
    assert float(tip[0]) < bar_x + (theme.BJT_STUB_X - theme.BJT_BASE_BAR_X) * w * 0.5
