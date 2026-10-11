"""Escala automáticamente el entrenamiento."""

from __future__ import annotations

from .models import TrainingPlan


class WorkoutScaler:
    """Ajusta duración e intensidad."""

    def scale(
        self,
        training: TrainingPlan,
        recovery: int,
        confidence: int,
    ) -> TrainingPlan:

        factor = 1.0

        if recovery >= 90:
            factor += 0.20
        elif recovery >= 80:
            factor += 0.10
        elif recovery <= 40:
            factor -= 0.30
        elif recovery <= 60:
            factor -= 0.15

        if confidence < 50:
            factor -= 0.10

        training.duration = max(
            20,
            int(training.duration * factor),
        )

        training.target_tss = max(
            10,
            int(training.target_tss * factor),
        )

        if training.intensity_factor is not None:
            training.intensity_factor *= factor

        return training