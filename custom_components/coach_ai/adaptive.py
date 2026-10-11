"""Planificador adaptativo."""

from __future__ import annotations

from .models import AthleteState


class AdaptivePlanner:
    """Ajusta el entrenamiento recomendado."""

    def choose(
        self,
        athlete: AthleteState,
        recovery: int,
        performance: int,
        risk: str,
        profile: str,
    ) -> str:

        if risk == "critical":
            return "rest"

        if recovery < 35:
            return "rest"

        if recovery < 50:
            return "recovery"

        if performance > 90:

            if profile == "elite":
                return "vo2max"

            return "threshold"

        if performance > 75:
            return "tempo"

        if performance > 55:
            return "endurance"

        return "recovery"