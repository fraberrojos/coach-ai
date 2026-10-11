"""Convierte GarminWorkout en FitWorkout."""

from __future__ import annotations

from .fit_models import FitStep
from .fit_models import FitWorkout
from .garmin_models import GarminWorkout
import logging

_LOGGER = logging.getLogger(__name__)

class FitBuilder:
    """Construye el modelo FIT."""

    def build(
        self,
        workout: GarminWorkout,
    ) -> FitWorkout:

        fit = FitWorkout(
            name=workout.name,
        )
        _LOGGER.debug("========== FIT BUILDER DEBUG ==========")
        _LOGGER.debug("GARMIN WORKOUT: %r", workout)
        _LOGGER.debug("GARMIN STEPS: %r", workout.steps)

        for step in workout.steps:

            if step.power_low is not None:

                target_type = "power"

                low = step.power_low
                high = step.power_high

            elif step.hr_low is not None:

                target_type = "heart_rate"

                low = step.hr_low
                high = step.hr_high

            elif step.cadence_low is not None:

                target_type = "cadence"

                low = step.cadence_low
                high = step.cadence_high

            else:

                target_type = "open"

                low = None
                high = None

            fit.steps.append(
                FitStep(
                    name=step.name,
                    duration=step.duration,
                    intensity=step.intensity,
                    target_type=target_type,
                    target_low=low,
                    target_high=high,
                    step_type=step.step_type,
                    repeat=step.repeat,
                )
            )

        return fit