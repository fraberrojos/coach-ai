"""Selector inteligente de entrenamientos."""

from __future__ import annotations

from .goal import GoalType


class WorkoutSelector:
    """Selecciona el tipo de entrenamiento."""

    # =============================================================
    # SELECCIÓN PRINCIPAL
    # =============================================================

    def select(
        self,
        goal: GoalType,
        recovery: int,
        fatigue: str,
        available_minutes: int,
    ) -> str:
        """Devuelve la clave del entrenamiento."""

        recovery = max(
            0,
            min(100, int(recovery)),
        )

        available_minutes = max(
            0,
            int(available_minutes),
        )

        # ---------------------------------------------------------
        # FATIGA CRÍTICA
        # ---------------------------------------------------------

        if fatigue == "Muy alta":
            return "recovery"

        # ---------------------------------------------------------
        # RECUPERACIÓN MUY BAJA
        # ---------------------------------------------------------

        if recovery < 30:
            return "recovery"

        # ---------------------------------------------------------
        # RECUPERACIÓN BAJA
        #
        # Evitamos trabajos intensos.
        # Si hay tiempo suficiente, preferimos Endurance suave
        # antes que llenar todo de Recovery.
        # ---------------------------------------------------------

        if recovery < 40:

            if available_minutes >= 60:
                return "endurance"

            return "recovery"

        # ---------------------------------------------------------
        # RECUPERACIÓN MODERADA-BAJA
        # ---------------------------------------------------------

        if recovery < 55:

            if goal == GoalType.WEIGHT_LOSS:
                return "endurance"

            if available_minutes >= 75:
                return "endurance"

            return "tempo"

        # ---------------------------------------------------------
        # FTP
        # ---------------------------------------------------------

        if goal == GoalType.FTP:

            if recovery >= 85:
                return "threshold"

            if recovery >= 70:
                return "sweet spot"

            return "tempo"

        # ---------------------------------------------------------
        # VO2 MAX
        # ---------------------------------------------------------

        if goal == GoalType.VO2MAX:

            if recovery >= 80:
                return "vo2 max"

            if recovery >= 65:
                return "sweet spot"

            return "endurance"

        # ---------------------------------------------------------
        # PÉRDIDA DE PESO
        # ---------------------------------------------------------

        if goal == GoalType.WEIGHT_LOSS:

            if recovery >= 70 and available_minutes >= 75:
                return "tempo"

            return "endurance"

        # ---------------------------------------------------------
        # MANTENIMIENTO / RESISTENCIA
        # ---------------------------------------------------------

        if goal == GoalType.ENDURANCE:

            if recovery >= 70 and available_minutes >= 75:
                return "tempo"

            return "endurance"

        # ---------------------------------------------------------
        # MANTENIMIENTO GENERAL
        # ---------------------------------------------------------

        if available_minutes >= 90:

            if recovery >= 70:
                return "endurance"

            return "endurance"

        if available_minutes >= 60:

            if recovery >= 55:
                return "tempo"

            return "endurance"

        # ---------------------------------------------------------
        # POCO TIEMPO
        # ---------------------------------------------------------

        if recovery >= 55:
            return "tempo"

        return "recovery"