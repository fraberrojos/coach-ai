"""Optimizador de entrenamientos."""

from __future__ import annotations

from .models import TrainingPlan


class OptimizerEngine:
    """Optimiza el entrenamiento."""

    def optimize(
        self,
        plan: TrainingPlan,
        recovery: int,
        risk: str,
    ) -> TrainingPlan:

        if risk == "critical":
            plan.duration = min(plan.duration, 30)
            plan.reason += " | Reducido por riesgo elevado."

        elif recovery < 40:
            plan.duration = int(plan.duration * 0.75)
            plan.reason += " | Duración reducida por baja recuperación."

        elif recovery > 85:
            plan.duration = int(plan.duration * 1.10)
            plan.reason += " | Sesión ampliada por excelente recuperación."

        return plan