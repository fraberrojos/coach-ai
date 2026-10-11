"""Adaptación según carga de entrenamiento."""

from __future__ import annotations


class TrainingLoadEngine:
    """Calcula el volumen recomendado."""

    def volume_factor(
        self,
        ctl: float,
        tsb: float,
    ) -> float:
        """Devuelve un multiplicador de volumen."""

        factor = 1.0

        if ctl >= 80:
            factor += 0.20
        elif ctl >= 60:
            factor += 0.10
        elif ctl < 30:
            factor -= 0.20

        if tsb < -20:
            factor -= 0.20
        elif tsb < -10:
            factor -= 0.10

        return max(0.6, min(1.3, factor))