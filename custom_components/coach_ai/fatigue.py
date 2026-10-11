"""Motor de fatiga acumulada."""

from __future__ import annotations


class FatigueEngine:
    """Calcula la fatiga acumulada."""

    def estimate(
        self,
        ctl: float | None,
        atl: float | None,
        tsb: float | None,
    ) -> int:
        """Devuelve una puntuación de 0 a 100."""

        if ctl is None or atl is None or tsb is None:
            return 50

        fatigue = atl - ctl

        if fatigue <= 0:
            return 15

        if fatigue <= 10:
            return 35

        if fatigue <= 20:
            return 55

        if fatigue <= 30:
            return 75

        return 95