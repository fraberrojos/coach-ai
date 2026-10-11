"""Motor de aprendizaje."""

from __future__ import annotations


class LearningEngine:
    """Aprende del historial."""

    def analyse(
        self,
        history: list[dict],
    ) -> dict[str, int]:

        stats = {
            "rest_days": 0,
            "training_days": 0,
        }

        for day in history:
            workout = (
                day.get("training", {})
                .get("workout", "")
            )

            if workout == "Descanso":
                stats["rest_days"] += 1
            elif workout:
                stats["training_days"] += 1

        return stats