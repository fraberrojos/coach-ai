"""Convierte TrainingPlan en un entrenamiento Garmin."""

from __future__ import annotations

import logging

from .garmin_models import GarminStep
from .garmin_models import GarminWorkout
from .models import TrainingPlan


_LOGGER = logging.getLogger(__name__)


class GarminBuilder:
    """Construye un entrenamiento Garmin respetando rangos y tipos de paso."""

    @staticmethod
    def _power_range(value):
        """Devuelve (mínimo, máximo) para potencia absoluta."""
        if value is None:
            return None, None

        if isinstance(value, (list, tuple)) and len(value) >= 2:
            try:
                low = float(value[0])
                high = float(value[1])
            except (TypeError, ValueError):
                return None, None
            return round(low), round(high)

        try:
            power = float(value)
        except (TypeError, ValueError):
            return None, None

        power = round(power)
        return power, power

    @staticmethod
    def _step_type(interval) -> str:
        """Usa step_type explícito y solo hace fallback al nombre."""
        explicit = str(getattr(interval, "step_type", "") or "").lower().strip()

        if explicit in {"warmup", "cooldown", "recovery", "interval"}:
            return explicit

        name_lower = str(getattr(interval, "name", "") or "").lower()

        if "calentamiento" in name_lower or name_lower == "warmup":
            return "warmup"

        if "vuelta a la calma" in name_lower or "enfriamiento" in name_lower:
            return "cooldown"

        if name_lower.startswith("recuper"):
            return "recovery"

        return "interval"

    def build(
        self,
        training: TrainingPlan,
    ) -> GarminWorkout:
        """Construye un GarminWorkout a partir del TrainingPlan."""

        workout = GarminWorkout(
            name=training.workout,
        )

        for interval in training.intervals:
            power_low, power_high = self._power_range(
                getattr(interval, "power", None)
            )

            heart_rate = getattr(interval, "heart_rate", None)
            cadence = getattr(interval, "cadence", None)

            if power_low is not None:
                target_type = "power"
            elif heart_rate is not None:
                target_type = "heart_rate"
            elif cadence is not None:
                target_type = "cadence"
            else:
                target_type = "open"

            step_type = self._step_type(interval)

            if step_type == "warmup":
                intensity = "warmup"
            elif step_type == "cooldown":
                intensity = "cooldown"
            elif step_type == "recovery":
                intensity = "rest"
            else:
                intensity = "active"

            step = GarminStep(
                name=str(interval.name),
                duration=int(interval.duration),
                target_type=target_type,
                power_low=power_low,
                power_high=power_high,
                hr_low=heart_rate,
                hr_high=heart_rate,
                cadence_low=cadence,
                cadence_high=cadence,
                step_type=step_type,
                repeat=1,
                intensity=intensity,
            )

            workout.steps.append(step)

            _LOGGER.debug(
                "Coach AI Garmin FTP STEP | name=%s | duration=%s | "
                "type=%s | target=%s | power=%s-%s",
                step.name,
                step.duration,
                step.step_type,
                step.target_type,
                step.power_low,
                step.power_high,
            )

        return workout
