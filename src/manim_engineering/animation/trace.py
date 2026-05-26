"""Animation pipeline tracing for teaching scenes (env-gated, zero overhead by default)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

TRACE_ENV = "ME_ANIMATION_TRACE"
TRACE_STDOUT_ENV = "ME_ANIMATION_TRACE_STDOUT"
SNAPSHOT_ENV = "ME_ANIMATION_SNAPSHOT"


def _debug_output_dir() -> Path:
    return Path(os.environ.get("DEBUG_SNAPSHOT_DIR", "media/debug"))


def trace_enabled() -> bool:
    return os.environ.get(TRACE_ENV, "") == "1"


def snapshot_enabled() -> bool:
    return os.environ.get(SNAPSHOT_ENV, "") == "1"


@dataclass(frozen=True)
class StageRecord:
    """One recorded checkpoint in the animation teaching pipeline."""

    stage: str
    beat_index: int | None
    signal_name: str | None
    run_time: float
    purpose: str | None
    detail: dict[str, object] = field(default_factory=dict)


class TracerProtocol(Protocol):
    def record(
        self,
        stage: str,
        *,
        beat_index: int | None = None,
        signal_name: str | None = None,
        run_time: float = 0.0,
        purpose: str | None = None,
        **detail: object,
    ) -> None: ...

    def flush(self, scene: object) -> Path | None: ...


class _NullTracer:
    def record(
        self,
        stage: str,
        *,
        beat_index: int | None = None,
        signal_name: str | None = None,
        run_time: float = 0.0,
        purpose: str | None = None,
        **detail: object,
    ) -> None:
        del stage, beat_index, signal_name, run_time, purpose, detail

    def flush(self, scene: object) -> Path | None:
        del scene
        return None


class AnimationTracer:
    """Collect stage records and write ``trace.json`` on flush."""

    def __init__(self, *, scene_name: str = "Scene") -> None:
        self._scene_name = scene_name
        self._records: list[StageRecord] = []

    def record(
        self,
        stage: str,
        *,
        beat_index: int | None = None,
        signal_name: str | None = None,
        run_time: float = 0.0,
        purpose: str | None = None,
        **detail: object,
    ) -> None:
        record = StageRecord(
            stage=stage,
            beat_index=beat_index,
            signal_name=signal_name,
            run_time=run_time,
            purpose=purpose,
            detail=dict(detail),
        )
        self._records.append(record)
        if os.environ.get(TRACE_STDOUT_ENV, "") == "1":
            parts = [stage]
            if beat_index is not None:
                parts.append(f"beat={beat_index}")
            if signal_name is not None:
                parts.append(f"signal={signal_name}")
            if run_time:
                parts.append(f"t={run_time:.2f}s")
            print("[animation-trace] " + " ".join(parts))

    def as_dict(self) -> dict[str, object]:
        return {
            "scene": self._scene_name,
            "stages": [
                {
                    "stage": record.stage,
                    "beat_index": record.beat_index,
                    "signal_name": record.signal_name,
                    "run_time": record.run_time,
                    "purpose": record.purpose,
                    "detail": record.detail,
                }
                for record in self._records
            ],
        }

    def dump_json(self, path: Path | None = None) -> str:
        payload = self.as_dict()
        text = json.dumps(payload, indent=2, default=str)
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return text

    def flush(self, scene: object) -> Path | None:
        if not self._records:
            return None
        scene_name = getattr(getattr(scene, "__class__", type(scene)), "__name__", "Scene")
        self._scene_name = scene_name
        target = _debug_output_dir() / scene_name / "trace.json"
        self.dump_json(target)
        self._records.clear()
        return target


_active_tracer: AnimationTracer | None = None
_null_tracer = _NullTracer()


def get_tracer() -> TracerProtocol:
    if not trace_enabled():
        return _null_tracer
    global _active_tracer
    if _active_tracer is None:
        _active_tracer = AnimationTracer()
    return _active_tracer


def reset_tracer() -> None:
    """Reset module tracer state before a new teaching scene construct."""
    global _active_tracer
    _active_tracer = None


def record_stage(
    stage: str,
    *,
    beat_index: int | None = None,
    signal_name: str | None = None,
    run_time: float = 0.0,
    purpose: str | None = None,
    **detail: object,
) -> None:
    get_tracer().record(
        stage,
        beat_index=beat_index,
        signal_name=signal_name,
        run_time=run_time,
        purpose=purpose,
        **detail,
    )


def flush_trace(scene: object) -> Path | None:
    return get_tracer().flush(scene)


def maybe_snapshot_stage(scene: object, label: str) -> Path | None:
    """Save PNG + JSON bounds when ``ME_ANIMATION_SNAPSHOT=1``."""
    if not snapshot_enabled():
        return None
    from manim_engineering.debug.snapshot import snapshot_frame, snapshot_topology

    snapshot_frame(scene, label)
    snapshot_topology(scene, label)
    scene_name = getattr(getattr(scene, "__class__", type(scene)), "__name__", "Scene")
    return _debug_output_dir() / scene_name
