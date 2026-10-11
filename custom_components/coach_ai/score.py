"""Motor de puntuación global."""

from __future__ import annotations


class ScoreEngine:
    """Calcula la puntuación global del deportista."""

    def calculate(
        self,
        recovery: int,
        fatigue: int,
        fitness: str,
    ) -> int:
        """Devuelve un Coach Score de 0 a 100."""

        score = recovery

        score -= fatigue // 5

        if fitness == "race_ready":
            score += 10
        elif fitness == "fit":
            score += 5
        elif fitness == "building":
            score += 0
        elif fitness == "detrained":
            score -= 10
        elif fitness == "overreached":
            score -= 15

        return max(0, min(100, score))