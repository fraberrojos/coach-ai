"""Trend Engine de Coach AI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class TrendResult:
    """Resultado del análisis del historial."""

    average_recovery: float
    recovery_trend: str
    fatigue_days: int
    consecutive_training_days: int
    risk_overtraining: bool
    training_load: str


class TrendEngine:
    """Analiza el historial del deportista."""

    def analyse(
        self,
        history: list[dict[str, Any]],
    ) -> TrendResult:
        """Analiza el historial."""

        # ========================================================
        # SIN HISTORIAL
        # ========================================================

        if not history:
            return TrendResult(
                average_recovery=0,
                recovery_trend="unknown",
                fatigue_days=0,
                consecutive_training_days=0,
                risk_overtraining=False,
                training_load="unknown",
            )

        # ========================================================
        # ÚLTIMOS 7 REGISTROS
        # ========================================================

        records = history[-7:]

        # ========================================================
        # RECOVERY
        # ========================================================

        recoveries: list[float] = []

        for item in records:

            if not isinstance(
                item,
                dict,
            ):
                continue

            analysis = item.get(
                "analysis"
            )

            if not isinstance(
                analysis,
                dict,
            ):
                continue

            recovery = analysis.get(
                "recovery_score"
            )

            if recovery is None:
                continue

            try:

                recovery_value = float(
                    recovery
                )

            except (
                TypeError,
                ValueError,
            ):

                continue

            recoveries.append(
                recovery_value
            )

        # ========================================================
        # MEDIA DE RECOVERY
        # ========================================================

        average = (
            sum(recoveries)
            / len(recoveries)
            if recoveries
            else 0
        )

        # ========================================================
        # TENDENCIA DE RECOVERY
        # ========================================================

        if len(recoveries) >= 2:

            if (
                recoveries[-1]
                > recoveries[0]
            ):

                trend = "improving"

            elif (
                recoveries[-1]
                < recoveries[0]
            ):

                trend = "declining"

            else:

                trend = "stable"

        else:

            trend = "stable"

        # ========================================================
        # DÍAS DE FATIGA
        # ========================================================

        fatigue_days = sum(
            1
            for value in recoveries
            if value < 50
        )

        # ========================================================
        # DÍAS DE ENTRENAMIENTO
        #
        # Antes dependíamos de:
        #
        # item["analysis"]["recommendation"]
        #
        # Ese campo ya no existe necesariamente en los registros
        # nuevos de HistoryManager.
        #
        # Ahora determinamos si existe entrenamiento mediante
        # el bloque "training".
        # ========================================================

        training_days = 0

        for item in records:

            if not isinstance(
                item,
                dict,
            ):
                continue

            training = item.get(
                "training"
            )

            if not isinstance(
                training,
                dict,
            ):
                continue

            workout = training.get(
                "workout"
            )

            # ----------------------------------------------------
            # Sin workout no contamos entrenamiento
            # ----------------------------------------------------

            if workout is None:
                continue

            workout_text = str(
                workout
            ).strip()

            if not workout_text:
                continue

            # ----------------------------------------------------
            # DESCANSO
            # ----------------------------------------------------

            if workout_text.lower() in {
                "descanso",
                "rest",
                "recovery",
                "recuperación",
            }:

                continue

            training_days += 1

        # ========================================================
        # RIESGO DE SOBREENTRENAMIENTO
        # ========================================================

        risk = (
            fatigue_days >= 3
            and training_days >= 5
        )

        # ========================================================
        # CARGA DE ENTRENAMIENTO
        # ========================================================

        if training_days >= 6:

            load = "very_high"

        elif training_days >= 5:

            load = "high"

        elif training_days >= 3:

            load = "medium"

        else:

            load = "low"

        # ========================================================
        # RESULTADO
        # ========================================================

        return TrendResult(
            average_recovery=round(
                average,
                1,
            ),
            recovery_trend=trend,
            fatigue_days=fatigue_days,
            consecutive_training_days=training_days,
            risk_overtraining=risk,
            training_load=load,
        )