"""Estimación del estado de forma."""

from __future__ import annotations


class FitnessEngine:
    """Calcula el estado de forma."""

    def estimate(
        self,
        ctl: float,
        atl: float,
        tsb: float,
    ) -> str:
        """Devuelve el estado del deportista."""

        if tsb < -25:
            return "overreached"

        if ctl > 70 and tsb > -10:
            return "race_ready"

        if ctl > 45:
            return "fit"

        if ctl > 20:
            return "building"

        return "detrained"