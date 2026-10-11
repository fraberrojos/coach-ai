"""Modelos internos para exportación Garmin."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class GarminStep:
    """Paso de un entrenamiento Garmin."""

    name: str
    duration: int

    target_type: str = "open"

    power_low: int | None = None
    power_high: int | None = None

    hr_low: int | None = None
    hr_high: int | None = None

    cadence_low: int | None = None
    cadence_high: int | None = None
    
    step_type: str = "interval"

    repeat: int = 1
    
    intensity: str = "active"


@dataclass(slots=True)
class GarminWorkout:
    """Entrenamiento completo."""

    name: str

    sport: str = "cycling"

    steps: list[GarminStep] = field(default_factory=list)