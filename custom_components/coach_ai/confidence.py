"""Nivel de confianza de Coach AI."""

from __future__ import annotations


class ConfidenceEngine:
    """Calcula la confianza del análisis."""

    def calculate(
        self,
        recovery: int,
        history_size: int,
        hrv: str | None,
        sleep: int | None,
    ) -> int:

        confidence = 50

        if recovery > 70:
            confidence += 15

        if history_size > 30:
            confidence += 15
        elif history_size > 7:
            confidence += 10

        if sleep is not None:
            confidence += 10

        if hrv not in (None, "", "Unknown"):
            confidence += 10

        return min(100, confidence)