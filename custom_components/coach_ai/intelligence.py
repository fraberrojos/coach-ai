"""Inteligencia de Coach AI."""

from __future__ import annotations


class IntelligenceEngine:
    """Genera conclusiones inteligentes."""

    def analyse(
        self,
        recovery: int,
        coach_score: int,
        fitness: str,
        fatigue: str,
        risk: str,
    ) -> str:

        if risk == "critical":
            return (
                "Existe un riesgo muy alto de sobreentrenamiento. "
                "Es recomendable descansar antes de continuar aumentando la carga."
            )

        if recovery >= 85 and fitness == "race_ready":
            return (
                "El organismo está preparado para afrontar un entrenamiento de máxima calidad."
            )

        if recovery >= 70 and fatigue == "Baja":
            return (
                "Buen momento para desarrollar rendimiento y aumentar la carga."
            )

        if recovery >= 50:
            return (
                "Estado estable. Mantén una carga moderada."
            )

        if recovery >= 35:
            return (
                "Conviene priorizar la recuperación antes de realizar intensidad."
            )

        return (
            "El organismo necesita descanso para evitar una acumulación excesiva de fatiga."
        )