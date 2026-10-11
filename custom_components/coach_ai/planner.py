"""Planificador de entrenamientos Coach AI."""

from __future__ import annotations

from .models import AthleteState
from .models import TrainingPlan
from .profile import ProfileEngine
from .training import TrainingEngine
from .weather import WeatherEngine


class PlannerEngine:
    """Planificador de entrenamientos."""

    def __init__(self) -> None:
        """Inicializa el planificador."""

        self.training_engine = TrainingEngine()
        self.profile_engine = ProfileEngine()
        self.weather_engine = WeatherEngine()

    # ============================================================
    # ELECCIÓN DEL ENTRENAMIENTO
    # ============================================================

    def choose(
        self,
        athlete: AthleteState,
        recovery_score: int,
    ) -> str:
        """Decide el entrenamiento más adecuado."""

        profile = self.profile_engine.classify(
            athlete
        )

        # --------------------------------------------------------
        # RECUPERACIÓN MUY BAJA
        # --------------------------------------------------------

        if recovery_score < 35:
            return "recovery"

        # --------------------------------------------------------
        # FATIGA ACUMULADA
        # --------------------------------------------------------

        if (
            athlete.tsb is not None
            and athlete.tsb < -20
        ):
            return "recovery"

        # --------------------------------------------------------
        # PRINCIPIANTE
        # --------------------------------------------------------

        if profile == "beginner":

            if recovery_score >= 70:
                return "endurance"

            return "recovery"

        # --------------------------------------------------------
        # INTERMEDIO
        # --------------------------------------------------------

        if profile == "intermediate":

            if recovery_score >= 80:
                return "tempo"

            if recovery_score >= 60:
                return "endurance"

            return "recovery"

        # --------------------------------------------------------
        # AVANZADO
        # --------------------------------------------------------

        if profile == "advanced":

            if recovery_score >= 85:
                return "threshold"

            if recovery_score >= 70:
                return "tempo"

            return "endurance"

        # --------------------------------------------------------
        # ÉLITE
        # --------------------------------------------------------

        if profile == "elite":

            if recovery_score >= 90:
                return "vo2_5x5"

            if recovery_score >= 80:
                return "threshold"

            if recovery_score >= 65:
                return "tempo"

            return "endurance"

        return "recovery"

    # ============================================================
    # HOY
    # ============================================================

    def today(
        self,
        athlete: AthleteState,
        recovery_score: int,
    ) -> TrainingPlan:
        """Genera el entrenamiento de hoy."""

        workout = self.choose(
            athlete,
            recovery_score,
        )

        outdoor, reason = (
            self.weather_engine.recommend(
                athlete
            )
        )

        training = (
            self.training_engine.generate(
                athlete,
                workout,
            )
        )

        if not outdoor:

            training.outdoor = False

            if reason:
                training.reason += (
                    f" {reason}"
                )

        return training

    # ============================================================
    # MAÑANA
    # ============================================================

    def tomorrow(
        self,
        athlete: AthleteState,
        recovery_score: int,
    ) -> TrainingPlan:
        """Genera el entrenamiento previsto para mañana."""

        return self.today(
            athlete,
            recovery_score,
        )

    # ============================================================
    # SEMANA
    # ============================================================

    def week(
        self,
        athlete: AthleteState,
        recovery_score: int,
    ) -> list[TrainingPlan]:
        """Genera un plan adaptativo de siete días."""

        plans: list[TrainingPlan] = []

        # --------------------------------------------------------
        # ESTADO BASE
        # --------------------------------------------------------

        base_recovery = max(
            0,
            min(
                100,
                int(recovery_score),
            ),
        )

        tsb = athlete.tsb or 0

        # --------------------------------------------------------
        # SEMANA DE RECUPERACIÓN
        # --------------------------------------------------------

        if (
            base_recovery < 40
            or tsb < -20
        ):

            workouts = [
                "recovery",
                "recovery",
                "endurance",
                "recovery",
                "endurance",
                "recovery",
                "recovery",
            ]

        # --------------------------------------------------------
        # SEMANA NORMAL
        # --------------------------------------------------------

        elif base_recovery < 70:

            workouts = [
                "recovery",
                "endurance",
                "recovery",
                "tempo",
                "recovery",
                "endurance",
                "recovery",
            ]

        # --------------------------------------------------------
        # SEMANA FAVORABLE
        # --------------------------------------------------------

        elif base_recovery < 85:

            workouts = [
                "recovery",
                "endurance",
                "tempo",
                "recovery",
                "threshold",
                "endurance",
                "recovery",
            ]

        # --------------------------------------------------------
        # SEMANA DE ALTO RENDIMIENTO
        # --------------------------------------------------------

        else:

            workouts = [
                "recovery",
                "endurance",
                "tempo",
                "recovery",
                "threshold",
                "endurance",
                "recovery",
            ]

        # --------------------------------------------------------
        # GENERAR SESIONES
        # --------------------------------------------------------

        for workout in workouts:

            try:

                training = (
                    self.training_engine.generate(
                        athlete,
                        workout,
                    )
                )

            except Exception:

                # Si algún tipo de entrenamiento no está
                # disponible, no dejamos la semana vacía.
                training = (
                    self.training_engine.generate(
                        athlete,
                        "recovery",
                    )
                )

                training.reason = (
                    "Sesión adaptada por Athena "
                    "para garantizar una carga segura."
                )

            plans.append(
                training
            )

        # --------------------------------------------------------
        # GARANTÍA DE SIETE DÍAS
        # --------------------------------------------------------

        while len(plans) < 7:

            try:

                plans.append(
                    self.training_engine.generate(
                        athlete,
                        "recovery",
                    )
                )

            except Exception:

                break

        return plans[:7]