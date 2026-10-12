"""Plan semanal fijo de running con ajustes prudentes por recuperación."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from .running_workout_builder import RunningWorkout, RunningWorkoutBuilder

RunningGoal = Literal["fitness", "5k", "10k", "half_marathon", "marathon"]


@dataclass(frozen=True, slots=True)
class RunningPlanDay:
    """Sesión asignada a un día de la semana (lunes=0)."""
    weekday: int
    workout_type: str
    duration_min: int
    priority: str = "normal"


@dataclass(slots=True)
class RunningWeekPlan:
    """Plan semanal con ajustes documentados."""
    week_start: date
    goal: RunningGoal
    sessions: list[RunningWorkout]
    scheduled_days: list[int]
    adjustments: list[str]


class RunningPlanner:
    """Plan fijo semanal; readiness modifica carga sin cambiar el objetivo."""
    BASE_DAYS = (1, 3, 6)  # martes, jueves y domingo

    def __init__(self, builder: RunningWorkoutBuilder | None = None) -> None:
        self.builder = builder or RunningWorkoutBuilder()

    def build_week(self, *, week_start: date, goal: RunningGoal = "fitness",
                   readiness: int | None = None, available_days: tuple[int, ...] | None = None,
                   usual_duration_min: int = 35) -> RunningWeekPlan:
        if week_start.weekday() != 0:
            raise ValueError("week_start debe ser lunes.")
        if goal not in {"fitness", "5k", "10k", "half_marathon", "marathon"}:
            raise ValueError(f"Objetivo de running no válido: {goal}")
        if readiness is not None and not 0 <= readiness <= 100:
            raise ValueError("readiness debe estar entre 0 y 100.")
        if usual_duration_min < 20:
            raise ValueError("La duración habitual debe ser de al menos 20 minutos.")

        days = list(self.BASE_DAYS)
        if available_days is not None:
            allowed = sorted({day for day in available_days if 0 <= day <= 6})
            days = [day for day in days if day in allowed]
            if not days:
                days = allowed[:3]
        adjustments: list[str] = []
        low_recovery = readiness is not None and readiness < 35
        reduced = readiness is not None and readiness < 60
        if low_recovery:
            adjustments.append("Recuperación baja: se sustituyen las sesiones exigentes por rodajes suaves.")
        elif reduced:
            adjustments.append("Readiness moderado: se reduce la duración y se evita la intensidad alta.")

        sessions: list[RunningWorkout] = []
        for index, _weekday in enumerate(days):
            if index == 0 and goal != "fitness" and not reduced:
                session = self.builder.intervals(
                    duration_min=max(40, usual_duration_min + 5),
                    repetitions=4 if goal in {"5k", "10k"} else 3,
                    effort_min=3, recovery_min=2,
                )
            else:
                multiplier = 1.25 if index == len(days) - 1 else 1.0
                if reduced:
                    multiplier *= 0.8 if not low_recovery else 0.7
                duration = max(20, round(usual_duration_min * multiplier))
                session = self.builder.easy_run(duration)
                if index == len(days) - 1:
                    session.name = "Rodaje largo suave"
                    session.workout_type = "long"
                elif index > 0:
                    session.name = "Rodaje de resistencia"
                    session.workout_type = "endurance"
            sessions.append(session)

        return RunningWeekPlan(week_start, goal, sessions, days, adjustments)
