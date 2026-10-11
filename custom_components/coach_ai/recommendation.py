"""Motor de recomendaciones."""

from __future__ import annotations


class RecommendationEngine:
    """Genera recomendaciones."""

    def build(
        self,
        decision: str,
        recovery: int,
        confidence: int,
    ) -> str:

        if decision == "REST":
            return "Descansa hoy para favorecer la recuperación."

        if decision == "RECOVERY":
            return "Realiza una sesión muy suave y prioriza la movilidad."

        if decision == "ENDURANCE":
            return "Entrenamiento aeróbico en Z2."

        if decision == "NORMAL_TRAINING":
            return "Entrenamiento planificado con normalidad."

        if decision == "HIGH_INTENSITY":
            if confidence >= 80:
                return "Día ideal para realizar la sesión más exigente."
            return "Puedes entrenar fuerte, aunque con cierta precaución."

        return "No hay suficiente información."