"""Training Engine de Coach AI."""

from __future__ import annotations

import logging

from .models import AthleteState
from .models import Interval
from .models import TrainingPlan
from .workout_library import WORKOUTS


_LOGGER = logging.getLogger(__name__)


class TrainingEngine:
    """Genera el entrenamiento."""

    @staticmethod
    def _duration_to_seconds(value: int | float) -> int:
        """Convierte una duración expresada en minutos a segundos."""
        try:
            minutes = float(value)
        except (TypeError, ValueError) as err:
            raise ValueError(
                f"Duración de intervalo no válida: {value!r}"
            ) from err

        if minutes <= 0:
            raise ValueError(
                f"La duración del intervalo debe ser mayor que 0 minutos: {value!r}"
            )

        seconds = int(round(minutes * 60))

        if seconds <= 0:
            raise ValueError(
                f"La duración convertida a segundos no es válida: {seconds}"
            )

        return seconds

    def generate(
        self,
        athlete: AthleteState,
        workout: str,
    ) -> TrainingPlan:
        """Genera el entrenamiento."""

        _LOGGER.error(
            "========== TRAINING ENGINE DEBUG =========="
        )

        _LOGGER.error(
            "WORKOUT SOLICITADO: %s",
            workout,
        )

        ftp = athlete.ftp or 250

        _LOGGER.error(
            "FTP UTILIZADO: %s",
            ftp,
        )

        data = WORKOUTS.get(
            workout,
            WORKOUTS["rest"],
        )

        _LOGGER.error(
            "WORKOUT DATA: %r",
            data,
        )

        raw_intervals = data.get("intervals", [])

        _LOGGER.error(
            "RAW INTERVALS: %r",
            raw_intervals,
        )

        intervals: list[Interval] = []

        for item in raw_intervals:
            power = None

            if item.get("power_factor") is not None:
                power = int(
                    ftp * item["power_factor"]
                )

            duration_seconds = self._duration_to_seconds(
                item["duration"]
            )

            interval = Interval(
                name=item["name"],
                duration=duration_seconds,
                power=power,
                cadence=item.get("cadence"),
            )

            intervals.append(interval)

            _LOGGER.error(
                "INTERVAL CREADO | nombre=%s | "
                "duracion_original=%s min | "
                "duracion_garmin=%s s | "
                "potencia=%s | cadencia=%s",
                interval.name,
                item["duration"],
                interval.duration,
                interval.power,
                interval.cadence,
            )

        target_power = None

        if data.get("power_factor") is not None:
            target_power = int(
                ftp * data["power_factor"]
            )

        training = TrainingPlan(
            workout=data["workout"],
            duration=data["duration"],
            zone=data["zone"],
            target_power=target_power,
            target_hr=None,
            cadence=data.get("cadence"),
            target_tss=data["target_tss"],
            intensity_factor=data["intensity_factor"],
            outdoor=data["outdoor"],
            reason=data["reason"],
            intervals=intervals,
        )

        _LOGGER.error(
            "TRAINING PLAN FINAL: %r",
            training,
        )

        _LOGGER.error(
            "TRAINING PLAN INTERVALS: %r",
            training.intervals,
        )

        _LOGGER.error(
            "============================================"
        )

        return training