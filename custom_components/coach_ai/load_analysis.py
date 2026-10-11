"""Análisis de carga de entrenamiento."""

from __future__ import annotations

class LoadEngine:
    """Analiza la carga del deportista."""

    def analyse(
        self,
        ctl: float | None,
        atl: float | None,
        tsb: float | None,
    ) -> dict[str, str]:

        ctl = ctl or 0
        atl = atl or 0
        tsb = tsb or 0

        if tsb < -25:
            status = "Sobrecarga"
        elif tsb < -10:
            status = "Carga alta"
        elif tsb <= 10:
            status = "Óptimo"
        else:
            status = "Muy descansado"

        if ctl < 20:
            progression = "Inicial"
        elif ctl < 45:
            progression = "Progresando"
        elif ctl < 75:
            progression = "Buen estado"
        else:
            progression = "Alto rendimiento"

        return {
            "status": status,
            "progression": progression,
        }

    # Compatibilidad con código antiguo
    def calculate(
        self,
        ctl: float | None,
        atl: float | None,
        tsb: float | None,
    ) -> dict[str, str]:
        return self.analyse(ctl, atl, tsb)