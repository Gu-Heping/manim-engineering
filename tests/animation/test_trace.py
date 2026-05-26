"""Animation pipeline trace (ME_ANIMATION_TRACE)."""

from __future__ import annotations

import json

import pytest

from manim_engineering.animation.trace import (
    flush_trace,
    get_tracer,
    record_stage,
    reset_tracer,
    trace_enabled,
)


@pytest.fixture(autouse=True)
def _reset_trace_state(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_tracer()
    monkeypatch.delenv("ME_ANIMATION_TRACE", raising=False)
    monkeypatch.delenv("ME_ANIMATION_TRACE_STDOUT", raising=False)
    yield
    reset_tracer()


def test_trace_disabled_by_default() -> None:
    assert trace_enabled() is False
    record_stage("intro.topology", run_time=1.0)
    assert flush_trace(object()) is None


def test_trace_records_stage_order_and_beat_index(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ME_ANIMATION_TRACE", "1")
    reset_tracer()

    record_stage("intro.topology", run_time=1.3, component_strokes=4)
    record_stage("hud.intro", run_time=1.05)
    record_stage(
        "sequence.beat_start",
        beat_index=0,
        signal_name="clk",
        run_time=1.2,
    )
    record_stage(
        "beat.play",
        beat_index=0,
        signal_name="clk",
        run_time=1.2,
        purpose="propagation",
    )
    record_stage("sequence.beat_end", beat_index=0, signal_name="clk", run_time=1.2)
    record_stage(
        "sequence.beat_start",
        beat_index=1,
        signal_name="data",
        run_time=1.2,
    )
    record_stage(
        "beat.play",
        beat_index=1,
        signal_name="data",
        run_time=1.2,
        purpose="propagation",
    )
    record_stage("sequence.beat_end", beat_index=1, signal_name="data", run_time=1.2)

    class DemoScene:
        pass

    path = flush_trace(DemoScene())
    assert path is not None
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["scene"] == "DemoScene"
    stages = [entry["stage"] for entry in payload["stages"]]
    assert stages[:2] == ["intro.topology", "hud.intro"]
    assert stages.count("sequence.beat_start") == 2
    assert stages.count("beat.play") == 2
    beat_indices = [
        entry["beat_index"]
        for entry in payload["stages"]
        if entry["stage"] == "beat.play"
    ]
    assert beat_indices == [0, 1]
    assert payload["stages"][2]["signal_name"] == "clk"


def test_trace_stdout_env(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("ME_ANIMATION_TRACE", "1")
    monkeypatch.setenv("ME_ANIMATION_TRACE_STDOUT", "1")
    reset_tracer()
    record_stage("hud.caption", beat_index=0, signal_name="clk", run_time=0.45)
    out = capsys.readouterr().out
    assert "[animation-trace]" in out
    assert "hud.caption" in out
    assert "beat=0" in out


def test_get_tracer_returns_null_when_disabled() -> None:
    tracer = get_tracer()
    tracer.record("noop")
    assert flush_trace(object()) is None
