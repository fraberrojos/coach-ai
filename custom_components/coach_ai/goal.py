"""Motor de objetivos de Coach AI."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GoalType(str, Enum):
    """Objetivos disponibles."""

    WEIGHT_LOSS = "weight_loss"
    ENDURANCE = "endurance"
    FTP = "ftp"
    VO2MAX = "vo2max"
    MAINTENANCE = "maintenance"
    EVENT = "event"


@dataclass(frozen=True)
class GoalProfile:
    """Configuración de un objetivo."""

    goal: GoalType
    name: str
    description: str
    preferred_training: str
    weekly_focus: str
    recovery_priority: int


class GoalEngine:
    """Motor encargado de adaptar el entrenamiento al objetivo."""

    def __init__(self) -> None:
        """Inicializa los objetivos."""

        self.goals = {
            GoalType.WEIGHT_LOSS: GoalProfile(
                goal=GoalType.WEIGHT_LOSS,
                name="Pérdida de peso",
                description=(
                    "Mejorar composición corporal manteniendo rendimiento."
                ),
                preferred_training="Z2 y resistencia aeróbica",
                weekly_focus="Volumen constante e intensidad controlada",
                recovery_priority=9,
            ),
            GoalType.ENDURANCE: GoalProfile(
                goal=GoalType.ENDURANCE,
                name="Resistencia",
                description="Mejorar capacidad aeróbica.",
                preferred_training="Rodajes largos Z2",
                weekly_focus="Aumentar volumen progresivamente",
                recovery_priority=8,
            ),
            GoalType.FTP: GoalProfile(
                goal=GoalType.FTP,
                name="Mejorar FTP",
                description="Aumentar potencia sostenible.",
                preferred_training="Sweet Spot y umbral",
                weekly_focus="Sesiones de calidad",
                recovery_priority=10,
            ),
            GoalType.VO2MAX: GoalProfile(
                goal=GoalType.VO2MAX,
                name="VO2 Max",
                description="Mejorar capacidad máxima.",
                preferred_training="Intervalos de alta intensidad",
                weekly_focus="Calidad sobre cantidad",
                recovery_priority=10,
            ),
            GoalType.MAINTENANCE: GoalProfile(
                goal=GoalType.MAINTENANCE,
                name="Mantenimiento",
                description="Mantener estado actual.",
                preferred_training="Entrenamiento equilibrado",
                weekly_focus="Constancia",
                recovery_priority=7,
            ),
            GoalType.EVENT: GoalProfile(
                goal=GoalType.EVENT,
                name="Preparación evento",
                description="Preparar una prueba concreta.",
                preferred_training="Simulación y carga específica",
                weekly_focus="Progresión hacia objetivo",
                recovery_priority=10,
            ),
        }

    def get_goal(
        self,
        goal: GoalType | str,
    ) -> GoalProfile:
        """Devuelve la configuración del objetivo."""

        if isinstance(goal, str):
             try:
                goal = GoalType(goal)
             except ValueError:
                goal = GoalType.MAINTENANCE

        return self.goals.get(
            goal, 
    self.goals[GoalType.MAINTENANCE],
    )
    def recommend_focus(
        self,
        goal: GoalType,
    ) -> str:
        """Devuelve el enfoque recomendado."""

        profile = self.get_goal(goal)

        return (
            f"{profile.name}: "
            f"{profile.preferred_training}. "
            f"Prioridad semanal: {profile.weekly_focus}"
        )