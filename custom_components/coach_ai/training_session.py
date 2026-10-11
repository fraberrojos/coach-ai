"""Sesión completa de entrenamiento."""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import Interval
from .models import TrainingPlan


@dataclass(slots=True)
class TrainingSession:
    """Entrenamiento completo generado por Coach AI."""

    plan: TrainingPlan

    estimated_tss: int

    intensity_factor: float

    calories: int

    hydration_ml: int

    carbs_per_hour: int

    expected_recovery: int

    confidence: int

    explanation: str

    intervals: list[Interval] = field(default_factory=list)