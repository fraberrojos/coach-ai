"""Definición de un entrenamiento."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class WorkoutDefinition:
    """Describe un entrenamiento."""

    name: str
    goal: str

    min_duration: int
    max_duration: int

    min_recovery: int

    target_tss: int
    intensity_factor: float

    priority: int

    # Nuevos campos

    workout_key: str
    zone: str
    cadence: int
    outdoor: bool
    reason: str
    power_factor: float | None = None