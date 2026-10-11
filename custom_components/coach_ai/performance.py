"""Motor de rendimiento."""

from __future__ import annotations


class PerformanceEngine:
    """Calcula un índice global de rendimiento."""

    def score(
        self,
        ctl: float | None,
        recovery: int,
        fitness: str,
        risk: str,
    ) -> int:

        score = 0

        ctl = ctl or 0

        # Estado físico
        if fitness == "race_ready":
            score += 35
        elif fitness == "fit":
            score += 28
        elif fitness == "building":
            score += 18
        else:
            score += 10

        # Recuperación
        score += int(recovery * 0.45)

        # Carga acumulada
        if ctl > 80:
            score += 20
        elif ctl > 60:
            score += 15
        elif ctl > 40:
            score += 10
        elif ctl > 20:
            score += 5

        # Riesgo
        if risk == "critical":
            score -= 25
        elif risk == "high":
            score -= 15
        elif risk == "medium":
            score -= 8

        return max(0, min(score, 100))