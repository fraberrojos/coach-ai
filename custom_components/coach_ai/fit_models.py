"""Modelos FIT."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class FitStep:
    """Paso de un entrenamiento FIT."""

    name: str

    duration: int

    intensity: str = "active"

    target_type: str = "open"

    target_low: int | None = None

    target_high: int | None = None
    
    step_type: str = "interval"

    repeat: int = 1


@dataclass(slots=True)
class FitWorkout:
    """Entrenamiento FIT."""

    name: str

    sport: str = "cycling"

    steps: list[FitStep] = field(default_factory=list)