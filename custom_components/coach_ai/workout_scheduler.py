"""Planificador semanal de Coach AI."""

from __future__ import annotations

from .goal import GoalType
from .models import AthleteState
from .models import TrainingPlan
from .weekly_pattern import WeeklyPattern
from .workout_context import WorkoutContext
from .workout_generator import WorkoutGenerator


class WorkoutScheduler:
    """Genera la planificación semanal."""

    def __init__(self) -> None:
        """Inicializa el planificador."""

        self.generator = WorkoutGenerator()

    def build_week(
        self,
        athlete: AthleteState,
        context: WorkoutContext,
        unavailable_days: set[int] | list[int] | None = None,
    ) -> list[TrainingPlan]:
        """Genera una semana de entrenamiento."""

        # El parámetro athlete forma parte de la interfaz pública
        # y queda preparado para futuras decisiones del scheduler.
        _ = athlete

        week: list[TrainingPlan] = []

        # =========================================================
        # DÍAS NO DISPONIBLES
        # =========================================================

        blocked_days = {
            int(day)
            for day in (unavailable_days or [])
            if isinstance(day, int)
            and 0 <= int(day) <= 6
        }

        # =========================================================
        # RECUPERACIÓN ESTIMADA POR DÍA
        # =========================================================

        recoveries = [
            context.recovery,
            max(
                context.recovery - 10,
                40,
            ),
            max(
                context.recovery - 5,
                40,
            ),
            max(
                context.recovery - 15,
                35,
            ),
            context.recovery,
            min(
                context.recovery + 5,
                100,
            ),
            max(
                context.recovery - 20,
                30,
            ),
        ]

        # =========================================================
        # PATRÓN SEMANAL SEGÚN OBJETIVO
        # =========================================================

        if context.goal == GoalType.FTP:

            pattern = WeeklyPattern.FTP

        elif context.goal == GoalType.VO2MAX:

            pattern = WeeklyPattern.VO2

        elif context.goal == GoalType.WEIGHT_LOSS:

            pattern = WeeklyPattern.WEIGHT_LOSS

        else:

            pattern = WeeklyPattern.ENDURANCE

        # =========================================================
        # GENERAR LOS 7 DÍAS
        # =========================================================

        for day_index in range(7):

            # -----------------------------------------------------
            # DÍA BLOQUEADO
            # -----------------------------------------------------

            if day_index in blocked_days:

                week.append(
                    self._create_unavailable_day()
                )

                continue

            # -----------------------------------------------------
            # ENTRENAMIENTO PREVISTO
            # -----------------------------------------------------

            preferred = None

            if day_index < len(pattern):

                preferred = pattern[day_index]

            # -----------------------------------------------------
            # CONTEXTO DEL DÍA
            # -----------------------------------------------------

            day_context = WorkoutContext(
                recovery=recoveries[day_index],
                readiness=context.readiness,
                fatigue=context.fatigue,
                fitness=context.fitness,
                goal=context.goal,
                available_minutes=(
                    context.available_minutes
                ),
                ctl=context.ctl,
                atl=context.atl,
                tsb=context.tsb,
                confidence=context.confidence,
                ftp=context.ftp,
                weather=context.weather,
                consistency=context.consistency,
                experience=context.experience,
            )

            # -----------------------------------------------------
            # REST
            #
            # No pasamos Rest por WorkoutGenerator.
            # -----------------------------------------------------

            if self._is_rest(preferred):

                week.append(
                    self._create_rest_day(
                        "Descanso planificado por "
                        "el patrón semanal."
                    )
                )

                continue

            # -----------------------------------------------------
            # GENERAR SESIÓN
            #
            # planning_mode=True es fundamental:
            # permite construir la semana base sin que la fatiga
            # global convierta todos los días en Recovery.
            # -----------------------------------------------------

            try:

                if preferred is not None:

                    training = self.generator.generate(
                        day_context,
                        preferred_workout=preferred,
                        planning_mode=True,
                    )

                else:

                    training = self.generator.generate(
                        day_context,
                        planning_mode=True,
                    )

            except TypeError:

                # Compatibilidad con versiones antiguas del
                # WorkoutGenerator.

                if preferred is not None:

                    training = self.generator.generate(
                        day_context,
                        preferred_workout=preferred,
                    )

                else:

                    training = self.generator.generate(
                        day_context,
                    )

            # -----------------------------------------------------
            # RESULTADO
            # -----------------------------------------------------

            if training is not None:

                week.append(training)

            else:

                week.append(
                    self._create_rest_day(
                        "Athena no ha generado sesión "
                        "para este día."
                    )
                )

        return week

    # =============================================================
    # REST
    # =============================================================

    @staticmethod
    def _is_rest(
        preferred: object,
    ) -> bool:
        """Determina si el patrón indica descanso."""

        if preferred is None:

            return False

        value = str(
            preferred
        ).strip().lower()

        return value in {
            "rest",
            "descanso",
            "rest day",
            "recovery rest",
        }

    @staticmethod
    def _create_rest_day(
        reason: str,
    ) -> TrainingPlan:
        """Crea un día de descanso real."""

        return TrainingPlan(
            workout="Rest",
            duration=0,
            zone="REST",
            target_power=None,
            target_hr=None,
            cadence=None,
            target_tss=0,
            intensity_factor=0.0,
            outdoor=False,
            reason=reason,
            intervals=[],
            export={},
        )

    # =============================================================
    # NO DISPONIBLE
    # =============================================================

    @staticmethod
    def _create_unavailable_day() -> TrainingPlan:
        """Crea un día no disponible."""

        return TrainingPlan(
            workout="Unavailable",
            duration=0,
            zone="REST",
            target_power=None,
            target_hr=None,
            cadence=None,
            target_tss=0,
            intensity_factor=0.0,
            outdoor=False,
            reason=(
                "🚫 Día no disponible. "
                "La sesión podrá ser recolocada por "
                "AdaptiveWeekEngine."
            ),
            intervals=[],
            export={},
        )