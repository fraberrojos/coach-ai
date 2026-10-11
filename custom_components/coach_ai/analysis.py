"""Análisis del último entrenamiento."""

from __future__ import annotations


class AnalysisEngine:
    """Analiza el último entrenamiento."""

    def analyse(
        self,
        target_tss: int | None,
        completed_tss: int | None,
    ) -> str:
        """Compara el objetivo con el entrenamiento realizado."""

        if target_tss is None or completed_tss is None:
            return "Sin datos"

        ratio = completed_tss / target_tss

        if ratio < 0.80:
            return "Entrenamiento insuficiente"

        if ratio < 1.10:
            return "Objetivo cumplido"

        return "Entrenamiento superior al previsto"