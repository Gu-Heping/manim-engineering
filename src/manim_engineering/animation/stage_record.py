from __future__ import annotations

from collections.abc import Callable

from .trace import record_stage


def record_plain_stage(
    stage: str,
    *,
    run_time: float,
    beat_index: int | None = None,
    signal_name: str | None = None,
    purpose: str | None = None,
    record: Callable[..., None] = record_stage,
    **detail: object,
) -> None:
    record(
        stage,
        beat_index=beat_index,
        signal_name=signal_name,
        run_time=run_time,
        purpose=purpose,
        **detail,
    )


def record_signal_stage(
    stage: str,
    *,
    signal_name: str,
    run_time: float,
    beat_index: int | None = None,
    purpose: str | None = None,
    record: Callable[..., None] = record_stage,
    **detail: object,
) -> None:
    record_plain_stage(
        stage,
        run_time=run_time,
        beat_index=beat_index,
        signal_name=signal_name,
        purpose=purpose,
        record=record,
        **detail,
    )


def wait_signal_stage(
    wait: Callable[[float], None],
    stage: str,
    *,
    signal_name: str,
    run_time: float,
    beat_index: int | None = None,
    purpose: str | None = None,
    record: Callable[..., None] = record_stage,
    **detail: object,
) -> None:
    record_signal_stage(
        stage,
        signal_name=signal_name,
        run_time=run_time,
        beat_index=beat_index,
        purpose=purpose,
        record=record,
        **detail,
    )
    wait(run_time)
