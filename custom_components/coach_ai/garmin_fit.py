"""Generador de entrenamientos Garmin FIT."""

from __future__ import annotations

from dataclasses import dataclass

from .models import TrainingPlan
from .export_models import WorkoutExport
from .export_models import WorkoutStep


@dataclass(slots=True)
class FitStep:
    """Paso de un entrenamiento FIT."""

    name: str
    duration: int
    target_type: str
    target_low: int | None
    target_high: int | None


class GarminFitBuilder:
    """Convierte un TrainingPlan en un entrenamiento Garmin."""

    def build(
        self,
        plan: TrainingPlan,
    ) -> WorkoutExport:

        steps: list[FitStep] = []

        for interval in plan.intervals:

            if interval.heart_rate is not None:
                target_type = "heart_rate"
                low = interval.heart_rate - 5
                high = interval.heart_rate + 5

            elif interval.power is not None:
                target_type = "power"
                low = interval.power - 5
                high = interval.power + 5

            elif interval.cadence is not None:
                target_type = "cadence"
                low = interval.cadence - 3
                high = interval.cadence + 3

            else:
                target_type = "open"
                low = None
                high = None

            steps.append(
                FitStep(
                    name=interval.name,
                    duration=interval.duration,
                    target_type=target_type,
                    target_low=low,
                    target_high=high,
                )
            )

        return WorkoutExport(
           name=plan.workout,
           description=plan.reason,
           sport="cycling",
           steps=[
               WorkoutStep(
                   name=s.name,
                   duration=s.duration,
                   target_type=s.target_type,
                   target_low=s.target_low,
                   target_high=s.target_high,
                )
                for s in steps
            ],
        )
                