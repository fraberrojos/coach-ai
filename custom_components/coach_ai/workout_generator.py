"""Generador inteligente de entrenamientos."""

from __future__ import annotations

from .goal import GoalType
from .models import Interval
from .models import TrainingPlan
from .workout_context import WorkoutContext
from .workout_library import WORKOUTS
from .workout_library import WorkoutLibrary
from .workout_selector import WorkoutSelector


class WorkoutGenerator:
    """Genera el entrenamiento ideal."""

    HARD_WORKOUTS = {
        "sweet spot",
        "threshold",
        "vo2 max",
    }

    def __init__(self) -> None:
        """Inicializa el generador."""

        self.library = WorkoutLibrary()
        self.selector = WorkoutSelector()

    # =============================================================
    # UTILIDADES
    # =============================================================

    @staticmethod
    def _calculate_power(
        ftp: float | None,
        power_factor: float | None,
    ) -> int | None:
        """Calcula la potencia objetivo a partir del FTP."""

        if ftp is None or power_factor is None:
            return None

        return round(ftp * power_factor)

    @staticmethod
    def _normalise_workout_key(
        workout_key: str,
    ) -> str:
        """Normaliza nombres de entrenamientos."""

        aliases = {
            "rest": "rest",
            "descanso": "rest",
            "recovery": "recovery",
            "recuperación": "recovery",
            "recuperacion": "recovery",
            "endurance": "endurance",
            "resistencia": "endurance",
            "long": "long ride",
            "long_ride": "long ride",
            "long ride": "long ride",
            "vo2": "vo2 max",
            "vo2max": "vo2 max",
            "vo2_max": "vo2 max",
            "vo2 max": "vo2 max",
            "sweetspot": "sweet spot",
            "sweet_spot": "sweet spot",
            "sweet spot": "sweet spot",
            "threshold": "threshold",
            "umbral": "threshold",
            "tempo": "tempo",
        }

        value = str(workout_key).strip().lower()

        return aliases.get(value, value)

    # =============================================================
    # INTERVALOS
    # =============================================================

    @staticmethod
    def _interval_step_type(
        name: str,
    ) -> str:
        """Determina el tipo de paso."""

        value = name.strip().lower()

        if any(
            word in value
            for word in (
                "calentamiento",
                "warmup",
                "warm-up",
            )
        ):
            return "warmup"

        if any(
            word in value
            for word in (
                "enfriamiento",
                "cooldown",
                "cool-down",
            )
        ):
            return "cooldown"

        if any(
            word in value
            for word in (
                "recovery",
                "recuperación",
                "recuperacion",
            )
        ):
            return "recovery"

        return "interval"

    @staticmethod
    def _build_intervals(
        workout_key: str,
        ftp: float | None,
        duration: int | None = None,
        power_scale: float = 1.0,
    ) -> list[Interval]:
        """Construye los intervalos del entrenamiento."""

        data = WORKOUTS.get(workout_key)

        if not data:
            return []

        source_intervals = data.get("intervals", [])

        if not source_intervals:
            return []

        original_total = sum(
            int(interval.get("duration", 0))
            for interval in source_intervals
        )

        if original_total <= 0:
            return []

        target_duration = (
            duration
            if duration is not None
            else original_total
        )

        target_duration = max(
            1,
            int(target_duration),
        )

        # ---------------------------------------------------------
        # Escalar duración manteniendo la estructura.
        # ---------------------------------------------------------

        ratio = target_duration / original_total

        durations: list[int] = []

        for interval in source_intervals:

            original_duration = int(
                interval.get("duration", 0)
            )

            durations.append(
                max(
                    1,
                    round(
                        original_duration * ratio
                    ),
                )
            )

        # ---------------------------------------------------------
        # Corregir redondeo para que la suma sea exactamente
        # la duración solicitada.
        # ---------------------------------------------------------

        difference = (
            target_duration
            - sum(durations)
        )

        if durations:
            durations[-1] = max(
                1,
                durations[-1] + difference,
            )

        # ---------------------------------------------------------
        # Crear objetos Interval.
        # ---------------------------------------------------------

        result: list[Interval] = []

        for index, interval in enumerate(
            source_intervals
        ):

            name = str(
                interval.get(
                    "name",
                    "Interval",
                )
            )

            power_factor = interval.get(
                "power_factor"
            )

            if power_factor is not None:

                power_factor = (
                    float(power_factor)
                    * power_scale
                )

            power = WorkoutGenerator._calculate_power(
                ftp,
                power_factor,
            )

            step_type = (
                WorkoutGenerator._interval_step_type(
                    name
                )
            )

            intensity = (
                "rest"
                if step_type == "recovery"
                else "active"
            )

            result.append(
                Interval(
                    name=name,
                    duration=durations[index],
                    power=power,
                    heart_rate=None,
                    cadence=interval.get(
                        "cadence"
                    ),
                    step_type=step_type,
                    intensity=intensity,
                )
            )

        return result

    # =============================================================
    # REST
    # =============================================================

    @staticmethod
    def _rest_day(
        reason: str = "Descanso programado por Athena.",
    ) -> TrainingPlan:
        """Genera un día de descanso real."""

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
    # RECOVERY
    # =============================================================

    @staticmethod
    def _recovery_day(
        context: WorkoutContext,
        reason: str,
        duration: int = 40,
    ) -> TrainingPlan:
        """Genera una sesión de recuperación."""

        available = (
            context.available_minutes
            or 40
        )

        duration = min(
            duration,
            available,
        )

        duration = max(
            20,
            duration,
        )

        target_power = WorkoutGenerator._calculate_power(
            context.ftp,
            0.45,
        )

        target_tss = max(
            1,
            round(duration * 0.50),
        )

        intervals = [
            Interval(
                name="Recovery",
                duration=duration,
                power=target_power,
                heart_rate=110,
                cadence=90,
                step_type="recovery",
                intensity="rest",
            )
        ]

        return TrainingPlan(
            workout="Recovery",
            duration=duration,
            zone="Z1",
            target_power=target_power,
            target_hr=110,
            cadence=90,
            target_tss=target_tss,
            intensity_factor=0.45,
            outdoor=False,
            reason=reason,
            intervals=intervals,
            export={},
        )

    # =============================================================
    # LONG RIDE
    # =============================================================

    def _long_ride(
        self,
        context: WorkoutContext,
    ) -> TrainingPlan:
        """Genera una sesión larga de resistencia."""

        available = (
            context.available_minutes
            or 90
        )

        duration = min(
            available,
            180,
        )

        duration = max(
            duration,
            60,
        )

        target_power = self._calculate_power(
            context.ftp,
            0.65,
        )

        target_tss = max(
            1,
            round(duration * 0.65),
        )

        intervals = [
            Interval(
                name="Zona 2",
                duration=duration,
                power=target_power,
                heart_rate=None,
                cadence=85,
                step_type="interval",
                intensity="active",
            )
        ]

        return TrainingPlan(
            workout="Long Ride",
            duration=duration,
            zone="Z2",
            target_power=target_power,
            target_hr=None,
            cadence=85,
            target_tss=target_tss,
            intensity_factor=0.65,
            outdoor=True,
            reason=(
                "Trabajo de resistencia y "
                "volumen aeróbico."
            ),
            intervals=intervals,
            export={},
        )

    # =============================================================
    # SCORE ATHENA
    # =============================================================

    @staticmethod
    def _athena_score(
        context: WorkoutContext,
    ) -> int:
        """Calcula el score interno de Athena."""

        score = 0.0

        score += context.recovery * 0.35
        score += context.confidence * 0.10
        score += context.consistency * 0.15
        score += min(context.ctl, 100) * 0.20

        if context.fatigue == "Muy alta":
            score -= 35

        elif context.fatigue == "Alta":
            score -= 20

        elif context.fatigue == "Media":
            score -= 10

        return max(
            0,
            min(100, int(score)),
        )

    # =============================================================
    # GENERADOR PRINCIPAL
    # =============================================================

    def generate(
        self,
        context: WorkoutContext,
        preferred_workout: str | None = None,
        planning_mode: bool = False,
    ) -> TrainingPlan:
        """Genera el entrenamiento óptimo.

        planning_mode=True se utiliza cuando Athena está
        construyendo la semana completa.

        En ese modo no se fuerza Recovery simplemente porque
        la fatiga global sea alta. La adaptación de la semana
        la realizará AdaptiveWeekEngine.
        """

        score = self._athena_score(context)

        # ---------------------------------------------------------
        # SELECCIÓN
        # ---------------------------------------------------------

        if preferred_workout is not None:

            workout_key = self._normalise_workout_key(
                preferred_workout
            )

        else:

            workout_key = self._normalise_workout_key(
                self.selector.select(
                    goal=context.goal,
                    recovery=context.recovery,
                    fatigue=context.fatigue,
                    available_minutes=(
                        context.available_minutes
                    ),
                )
            )

        # ---------------------------------------------------------
        # REST
        # ---------------------------------------------------------

        if workout_key == "rest":

            return self._rest_day(
                "Descanso programado por Athena."
            )

        # ---------------------------------------------------------
        # RECUPERACIÓN CRÍTICA
        #
        # Solo se aplica automáticamente fuera de la
        # planificación semanal.
        # ---------------------------------------------------------

        if (
            not planning_mode
            and (
                context.recovery < 30
                or context.fatigue == "Muy alta"
            )
        ):

            return self._recovery_day(
                context,
                (
                    f"Athena Score {score}/100. "
                    "Recuperación prioritaria."
                ),
                duration=min(
                    40,
                    context.available_minutes or 40,
                ),
            )

        # ---------------------------------------------------------
        # ENTRENAMIENTOS DUROS
        #
        # Incluso durante la planificación semanal protegemos
        # los entrenamientos intensos si la recuperación es
        # insuficiente.
        # ---------------------------------------------------------

        if workout_key in self.HARD_WORKOUTS:

            if context.recovery < 40:

                return self._recovery_day(
                    context,
                    (
                        f"Athena Score {score}/100. "
                        f"{workout_key.title()} sustituido "
                        "por recuperación debido a "
                        "recuperación baja."
                    ),
                    duration=min(
                        35,
                        context.available_minutes or 35,
                    ),
                )

            if context.recovery < 55:

                power_scale = 0.90

            elif context.recovery < 70:

                power_scale = 0.95

            else:

                power_scale = 1.0

        else:

            power_scale = 1.0

        # ---------------------------------------------------------
        # LONG RIDE
        # ---------------------------------------------------------

        if workout_key == "long ride":

            if context.recovery < 40:

                return self._recovery_day(
                    context,
                    (
                        f"Athena Score {score}/100. "
                        "Long Ride sustituido por "
                        "recuperación."
                    ),
                    duration=min(
                        35,
                        context.available_minutes or 35,
                    ),
                )

            if context.recovery < 60:

                duration = min(
                    context.available_minutes or 120,
                    120,
                )

            else:

                duration = min(
                    context.available_minutes or 180,
                    180,
                )

            duration = max(
                60,
                duration,
            )

            return self._long_ride(
                WorkoutContext(
                    recovery=context.recovery,
                    readiness=context.readiness,
                    fatigue=context.fatigue,
                    fitness=context.fitness,
                    goal=context.goal,
                    available_minutes=duration,
                    ctl=context.ctl,
                    atl=context.atl,
                    tsb=context.tsb,
                    confidence=context.confidence,
                    ftp=context.ftp,
                    weather=context.weather,
                    consistency=context.consistency,
                    experience=context.experience,
                )
            )

        # ---------------------------------------------------------
        # MAPA DE OBJETIVOS
        # ---------------------------------------------------------

        goal_map = {
            "recovery": "recovery",
            "endurance": "maintenance",
            "tempo": "maintenance",
            "sweet spot": "ftp",
            "threshold": "ftp",
            "vo2 max": "vo2",
        }

        goal = goal_map.get(
            workout_key,
            "maintenance",
        )

        # ---------------------------------------------------------
        # DEFINICIÓN EXACTA
        # ---------------------------------------------------------

        definition = next(
            (
                workout
                for workout in self.library.workouts
                if workout.workout_key == workout_key
            ),
            None,
        )

        # ---------------------------------------------------------
        # ALTERNATIVA
        # ---------------------------------------------------------

        if definition is None:

            definition = self.library.search(
                goal=goal,
                duration=(
                    context.available_minutes or 60
                ),
                recovery=context.recovery,
            )

            workout_key = definition.workout_key

        # ---------------------------------------------------------
        # DURACIÓN
        # ---------------------------------------------------------

        available = (
            context.available_minutes
            or 60
        )

        duration = min(
            available,
            definition.max_duration,
        )

        duration = max(
            duration,
            definition.min_duration,
        )

        # ---------------------------------------------------------
        # REDUCCIÓN POR RECUPERACIÓN
        # ---------------------------------------------------------

        duration_scale = 1.0

        if context.recovery < 40:

            duration_scale = 0.75

        elif context.recovery < 55:

            duration_scale = 0.80

        elif context.recovery < 70:

            duration_scale = 0.90

        if workout_key in self.HARD_WORKOUTS:

            duration = max(
                definition.min_duration,
                int(
                    duration
                    * duration_scale
                ),
            )

        # ---------------------------------------------------------
        # POTENCIA
        # ---------------------------------------------------------

        base_power_factor = (
            definition.power_factor
        )

        effective_power_factor = (
            base_power_factor
            * power_scale
        )

        target_power = self._calculate_power(
            context.ftp,
            effective_power_factor,
        )

        # ---------------------------------------------------------
        # TSS
        # ---------------------------------------------------------

        target_tss = max(
            1,
            round(
                definition.target_tss
                * duration_scale
                * power_scale
            ),
        )

        intensity_factor = round(
            definition.intensity_factor
            * power_scale,
            3,
        )

        # ---------------------------------------------------------
        # INTERVALOS
        # ---------------------------------------------------------

        intervals = self._build_intervals(
            workout_key=workout_key,
            ftp=context.ftp,
            duration=duration,
            power_scale=power_scale,
        )

        # ---------------------------------------------------------
        # RAZÓN
        # ---------------------------------------------------------

        reason = (
            f"Athena Score {score}/100. "
            f"Sesión {definition.name}."
        )

        if duration_scale < 1.0:

            reason += (
                " Duración reducida por "
                "recuperación."
            )

        if power_scale < 1.0:

            reason += (
                " Intensidad reducida."
            )

        # ---------------------------------------------------------
        # RESULTADO
        # ---------------------------------------------------------

        return TrainingPlan(
            workout=definition.name,
            duration=duration,
            zone=definition.zone,
            target_power=target_power,
            target_hr=None,
            cadence=definition.cadence,
            target_tss=target_tss,
            intensity_factor=intensity_factor,
            outdoor=definition.outdoor,
            reason=reason,
            intervals=intervals,
            export={},
        )