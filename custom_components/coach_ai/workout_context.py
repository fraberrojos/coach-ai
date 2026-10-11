"""Contexto para generar un entrenamiento."""

from __future__ import annotations

from dataclasses import dataclass

from .goal import GoalType


@dataclass(slots=True)
class WorkoutContext:
    """Información necesaria para generar un entrenamiento."""

    recovery: int
    readiness: str
    fatigue: str

    fitness: str

    goal: GoalType

    available_minutes: int

    ctl: float
    atl: float
    tsb: float

    confidence: int

    # FTP actual del ciclista.
    ftp: float | None = None

    weather: str = ""

    consistency: int = 0

    experience: str = ""