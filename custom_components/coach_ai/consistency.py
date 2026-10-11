"""Motor de consistencia."""

from __future__ import annotations


class ConsistencyEngine:
    """Analiza la regularidad de entrenamiento."""

    def analyse(
        self,
        history: list[dict],
    ) -> tuple[int, str]:

        sessions = 0

        for day in history[-14:]:

            workout = (
                day.get("training", {})
                .get("workout")
            )

            if workout and workout != "Descanso":
                sessions += 1

        score = min(100, sessions * 14)

        if score >= 85:
            level = "Excelente"
        elif score >= 65:
            level = "Buena"
        elif score >= 40:
            level = "Irregular"
        else:
            level = "Muy baja"

        return score, level