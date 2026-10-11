"""Tendencia de fatiga."""

from __future__ import annotations


class FatigueTrendEngine:
    """Calcula la tendencia de la fatiga."""

    def analyse(
        self,
        history: list[dict],
    ) -> str:

        if len(history) < 3:
            return "stable"

        values = [
            h["analysis"]["recovery_score"]
            for h in history[-3:]
            if "analysis" in h
        ]

        if len(values) < 3:
            return "stable"

        if values[-1] > values[0] + 8:
            return "improving"

        if values[-1] < values[0] - 8:
            return "declining"

        return "stable"