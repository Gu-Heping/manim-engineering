"""NPN common-emitter preset layout tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from manim_engineering.layout.footprint import assert_wires_avoid_footprints
from manim_engineering.layout.presets.npn_ce import RC_STUB_X, RE_STUB_X, SPINE_X

REPO = Path(__file__).resolve().parents[2]


def _load_fixture():
    spec = importlib.util.spec_from_file_location(
        "fixture", REPO / "examples/analog/04_npn_amplifier.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.build_npn_amplifier_fixture()


def test_npn_spine_stubs_separate_resistors_from_bus() -> None:
    _graph, elements, layout = _load_fixture()
    rc_b = layout.pin_positions[elements["rc1"].get_pin("b").id]
    collector = layout.pin_positions[elements["q1"].get_pin("collector").id]
    re_a = layout.pin_positions[elements["re1"].get_pin("a").id]
    emitter = layout.pin_positions[elements["q1"].get_pin("emitter").id]

    assert rc_b.x == pytest.approx(RC_STUB_X)
    assert collector.x == pytest.approx(SPINE_X)
    assert rc_b.x < collector.x
    assert re_a.x == pytest.approx(RE_STUB_X)
    assert emitter.x == pytest.approx(SPINE_X)
    assert re_a.x > emitter.x

    rc_stub = next(
        w for w in layout.wires if "rc1.b" in w.connection_id and "collector" in w.connection_id
    )
    assert len(rc_stub.segments) == 1
    assert rc_stub.segments[0].start.y == rc_stub.segments[0].end.y

    emitter_stub = next(
        w for w in layout.wires if "re1.a" in w.connection_id and "emitter" in w.connection_id
    )
    assert len(emitter_stub.segments) == 1
    assert emitter_stub.segments[0].start.y == emitter_stub.segments[0].end.y

    assert_wires_avoid_footprints(layout)


def test_npn_vcc_rc_horizontal_rail() -> None:
    _graph, elements, layout = _load_fixture()
    vcc_pin = layout.pin_positions[elements["vcc1"].get_pin("vcc").id]
    rc_a = layout.pin_positions[elements["rc1"].get_pin("a").id]
    assert vcc_pin.y == pytest.approx(rc_a.y)
    assert vcc_pin.x < rc_a.x - 0.4

    vcc_wire = next(
        w for w in layout.wires if "vcc" in w.connection_id and "rc1.a" in w.connection_id
    )
    assert len(vcc_wire.segments) == 1
    seg = vcc_wire.segments[0]
    assert seg.start.y == seg.end.y == pytest.approx(vcc_pin.y)
    assert seg.start.x == pytest.approx(vcc_pin.x)
    assert seg.end.x == pytest.approx(rc_a.x)


def test_npn_collector_stub_does_not_cross_rc_body() -> None:
    _graph, elements, layout = _load_fixture()
    rc = elements["rc1"]
    rc_b = layout.pin_positions[rc.get_pin("b").id]
    collector = layout.pin_positions[elements["q1"].get_pin("collector").id]
    stub = next(
        w for w in layout.wires if "rc1.b" in w.connection_id and "collector" in w.connection_id
    )
    for seg in stub.segments:
        assert seg.start.y == seg.end.y == collector.y
        lo, hi = sorted((seg.start.x, seg.end.x))
        assert lo >= rc_b.x - 1e-6
        assert hi <= collector.x + 1e-6
