"""Modelo del deportista."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AthleteState:
    """Estado fisiológico del deportista."""

    body_battery: int | None = None

    sleep_score: int | None = None

    stress: int | None = None

    training_readiness: int | None = None

    hrv_status: str | None = None

    ftp: int | None = None

    vo2max: int | None = None

    ctl: int | None = None

    atl: int | None = None

    tsb: int | None = None

    resting_hr: int | None = None

    max_hr: int | None = None

    weight: float | None = None