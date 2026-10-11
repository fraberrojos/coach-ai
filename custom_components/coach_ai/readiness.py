"""Training Readiness."""

from __future__ import annotations


class ReadinessEngine:
    """Calcula la disponibilidad para entrenar."""

    def calculate(
        self,
        recovery: int,
        fatigue: str,
        risk: str,
    ) -> str:

        if risk == "critical":
            return "Do Not Train"

        if recovery >= 85 and fatigue == "Baja":
            return "Peak"

        if recovery >= 70:
            return "Ready"

        if recovery >= 50:
            return "Moderate"

        if recovery >= 35:
            return "Easy Only"

        return "Recovery"