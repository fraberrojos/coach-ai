"""Aprendizaje de la adaptación del deportista."""

from __future__ import annotations


class AdaptationEngine:
    """Calcula cómo adaptar la carga futura."""

    def factor(
        self,
        success_rate: float,
    ) -> float:
        """Devuelve un factor de ajuste."""

        if success_rate >= 0.95:
            return 1.05

        if success_rate >= 0.85:
            return 1.00

        if success_rate >= 0.70:
            return 0.95

        return 0.90