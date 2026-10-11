"""Motor de periodización."""

from __future__ import annotations


class PeriodizationEngine:
    """Genera el tipo de entrenamiento según el día."""

    def workout_type(
        self,
        day: int,
    ) -> str:
        """
        day:
        0=Lunes
        ...
        6=Domingo
        """

        schedule = {
            0: "recovery",
            1: "tempo",
            2: "endurance",
            3: "threshold",
            4: "recovery",
            5: "long",
            6: "endurance",
        }

        return schedule.get(day, "endurance")