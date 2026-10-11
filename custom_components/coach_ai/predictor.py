"""Predicción de riesgo."""

from __future__ import annotations


class PredictorEngine:
    """Predice el riesgo de sobreentrenamiento."""

    def risk(
        self,
        ctl: float | None,
        atl: float | None,
        tsb: float | None,
        recovery: int,
    ) -> tuple[str, int]:

        ctl = ctl or 0
        atl = atl or 0
        tsb = tsb or 0

        score = 0

        if recovery < 40:
            score += 35

        if atl > ctl + 15:
            score += 30

        if tsb < -20:
            score += 25

        if ctl > 80:
            score += 10

        score = min(score, 100)

        if score >= 80:
            return "critical", score

        if score >= 60:
            return "high", score

        if score >= 40:
            return "medium", score

        return "low", score