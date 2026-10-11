"""Planificador de temporada."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(slots=True)
class SeasonWeek:
    """Representa una semana de entrenamiento."""

    week: int
    phase: str
    objective: str
    target_tss: int


class SeasonPlanner:
    """Genera una planificación básica."""

    def build(self) -> list[SeasonWeek]:

        return [

            SeasonWeek(
                week=1,
                phase="Base",
                objective="Resistencia",
                target_tss=350,
            ),

            SeasonWeek(
                week=2,
                phase="Base",
                objective="Resistencia",
                target_tss=380,
            ),

            SeasonWeek(
                week=3,
                phase="Construcción",
                objective="Sweet Spot",
                target_tss=450,
            ),

            SeasonWeek(
                week=4,
                phase="Descarga",
                objective="Recuperación",
                target_tss=250,
            ),

        ]