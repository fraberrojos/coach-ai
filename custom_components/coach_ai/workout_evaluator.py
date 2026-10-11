"""Evaluador de entrenamientos de Coach AI."""

from __future__ import annotations

from dataclasses import dataclass

from .models import ActivitySummary, TrainingPlan


@dataclass(slots=True)
class WorkoutEvaluation:
    """Resultado de la evaluación de una sesión real."""

    status: str
    score: float
    completion_percent: float

    duration_real: int | None
    duration_target: int | None

    tss_real: float | None
    tss_target: float | None

    power_real: int | None
    heart_rate_real: int | None

    feedback: str


class WorkoutEvaluator:
    """Evalúa entrenamientos planificados y realizados."""

    # A partir de este porcentaje se considera que el entrenamiento
    # se ha cumplido de forma suficiente.
    COMPLETE_THRESHOLD = 0.85

    # Por debajo de este porcentaje se considera no completado.
    PARTIAL_THRESHOLD = 0.55

    # Pesos de la evaluación real.
    # Duración = cumplimiento temporal.
    # TSS = carga realmente generada.
    # Intensidad = potencia o FC respecto al objetivo.
    DURATION_WEIGHT = 0.30
    TSS_WEIGHT = 0.40
    INTENSITY_WEIGHT = 0.30

    # ============================================================
    # EVALUACIÓN INTERNA DE ATHENA
    # ============================================================

    def evaluate(
        self,
        workout: TrainingPlan | None,
    ) -> tuple[int, str]:
        """Evalúa la calidad del entrenamiento planificado.

        Este método mantiene la compatibilidad con Athena.
        """

        if workout is None:
            return 0, "Sin entrenamiento"

        score = 100

        # --------------------------------------------------------
        # DURACIÓN
        # --------------------------------------------------------

        if workout.duration <= 0:

            if workout.workout == "Rest":
                return 100, "Descanso"

            return 50, "Sin duración"

        # --------------------------------------------------------
        # TSS
        # --------------------------------------------------------

        if workout.target_tss is None:
            score -= 5

        elif workout.target_tss <= 0:
            score -= 5

        # --------------------------------------------------------
        # POTENCIA / FC
        # --------------------------------------------------------

        if (
            workout.target_power is None
            and workout.target_hr is None
        ):
            score -= 5

        # --------------------------------------------------------
        # INTERVALOS
        # --------------------------------------------------------

        if workout.intervals:

            valid_intervals = [
                interval
                for interval in workout.intervals
                if interval.duration > 0
            ]

            if not valid_intervals:
                score -= 10

        # --------------------------------------------------------
        # ZONA
        # --------------------------------------------------------

        if not workout.zone:
            score -= 5

        # --------------------------------------------------------
        # LIMITAR
        # --------------------------------------------------------

        score = max(
            0,
            min(
                100,
                score,
            ),
        )

        # --------------------------------------------------------
        # CALIDAD
        # --------------------------------------------------------

        if score >= 90:
            quality = "Excelente"

        elif score >= 75:
            quality = "Buena"

        elif score >= 60:
            quality = "Aceptable"

        elif score >= 40:
            quality = "Baja"

        else:
            quality = "Muy baja"

        return score, quality

    # ============================================================
    # UTILIDADES
    # ============================================================

    @staticmethod
    def _safe_ratio(
        real: float | int | None,
        target: float | int | None,
        default: float = 0.0,
        maximum: float = 1.20,
    ) -> float:
        """Calcula real/objetivo y limita el resultado."""

        if (
            real is None
            or target is None
            or float(target) <= 0
        ):
            return default

        ratio = float(real) / float(target)

        return max(
            0.0,
            min(
                ratio,
                maximum,
            ),
        )

    @staticmethod
    def _percent_difference(
        real: float | int | None,
        target: float | int | None,
    ) -> float | None:
        """Devuelve la diferencia porcentual real respecto al objetivo."""

        if (
            real is None
            or target is None
            or float(target) <= 0
        ):
            return None

        return (
            (float(real) - float(target))
            / float(target)
        ) * 100.0

    # ============================================================
    # EVALUACIÓN REAL GARMIN
    # ============================================================

    def evaluate_real(
        self,
        workout: TrainingPlan | None,
        activity: ActivitySummary | None,
    ) -> WorkoutEvaluation:
        """Compara un entrenamiento planificado con Garmin.

        La evaluación combina:
        - 30 % duración.
        - 40 % TSS.
        - 30 % intensidad (potencia o FC).

        Si no existe un objetivo de intensidad, el peso de intensidad
        se redistribuye entre duración y TSS.
        """

        # --------------------------------------------------------
        # SIN ENTRENAMIENTO
        # --------------------------------------------------------

        if workout is None:

            return WorkoutEvaluation(
                status="EXTRA",
                score=0.0,
                completion_percent=0.0,
                duration_real=(
                    activity.duration
                    if activity
                    else None
                ),
                duration_target=None,
                tss_real=(
                    activity.training_load
                    if activity
                    else None
                ),
                tss_target=None,
                power_real=(
                    activity.avg_power
                    if activity
                    else None
                ),
                heart_rate_real=(
                    activity.avg_hr
                    if activity
                    else None
                ),
                feedback=(
                    "Actividad realizada fuera "
                    "del entrenamiento planificado."
                ),
            )

        # --------------------------------------------------------
        # SIN ACTIVIDAD
        # --------------------------------------------------------

        if activity is None:

            return WorkoutEvaluation(
                status="NOT_COMPLETED",
                score=0.0,
                completion_percent=0.0,
                duration_real=None,
                duration_target=workout.duration,
                tss_real=None,
                tss_target=(
                    float(workout.target_tss)
                    if workout.target_tss is not None
                    else None
                ),
                power_real=None,
                heart_rate_real=None,
                feedback=(
                    "No se ha detectado una actividad "
                    "de Garmin para esta sesión."
                ),
            )

        # --------------------------------------------------------
        # DATOS BÁSICOS
        # --------------------------------------------------------

        target_duration = workout.duration
        real_duration = activity.duration

        target_tss = (
            float(workout.target_tss)
            if workout.target_tss is not None
            else None
        )

        real_tss = activity.training_load

        target_power = getattr(
            workout,
            "target_power",
            None,
        )

        target_hr = getattr(
            workout,
            "target_hr",
            None,
        )

        real_power = activity.avg_power
        real_hr = activity.avg_hr

        # --------------------------------------------------------
        # DURACIÓN
        # --------------------------------------------------------

        duration_ratio = self._safe_ratio(
            real_duration,
            target_duration,
        )

        # --------------------------------------------------------
        # TSS
        # --------------------------------------------------------

        tss_available = (
            target_tss is not None
            and target_tss > 0
            and real_tss is not None
        )

        if tss_available:

            tss_ratio = self._safe_ratio(
                real_tss,
                target_tss,
            )

        else:

            tss_ratio = duration_ratio

        # --------------------------------------------------------
        # INTENSIDAD
        # --------------------------------------------------------
        # Preferimos potencia cuando existe objetivo de potencia.
        # Si no existe, utilizamos frecuencia cardíaca.

        intensity_ratio = None
        intensity_type = None
        intensity_target = None
        intensity_real = None

        if (
            target_power is not None
            and float(target_power) > 0
            and real_power is not None
        ):

            intensity_ratio = self._safe_ratio(
                real_power,
                target_power,
            )

            intensity_type = "potencia"
            intensity_target = float(target_power)
            intensity_real = float(real_power)

        elif (
            target_hr is not None
            and float(target_hr) > 0
            and real_hr is not None
        ):

            intensity_ratio = self._safe_ratio(
                real_hr,
                target_hr,
            )

            intensity_type = "frecuencia cardíaca"
            intensity_target = float(target_hr)
            intensity_real = float(real_hr)

        # --------------------------------------------------------
        # CUMPLIMIENTO
        # --------------------------------------------------------

        if intensity_ratio is not None:

            completion_ratio = (
                duration_ratio * self.DURATION_WEIGHT
                + tss_ratio * self.TSS_WEIGHT
                + intensity_ratio * self.INTENSITY_WEIGHT
            )

        else:
            # Si no hay objetivo de potencia ni FC, no penalizamos
            # artificialmente la sesión por falta de ese dato.
            base_weight = (
                self.DURATION_WEIGHT
                + self.TSS_WEIGHT
            )

            completion_ratio = (
                duration_ratio * self.DURATION_WEIGHT
                + tss_ratio * self.TSS_WEIGHT
            ) / base_weight

        completion_ratio = max(
            0.0,
            min(
                completion_ratio,
                1.0,
            ),
        )

        completion_percent = round(
            completion_ratio * 100,
            1,
        )

        # --------------------------------------------------------
        # SCORE
        # --------------------------------------------------------

        # El score representa directamente el grado de cumplimiento
        # de la sesión, en una escala de 0 a 10.
        score = round(
            completion_ratio * 10,
            1,
        )

        feedback_parts: list[str] = []

        # --------------------------------------------------------
        # INTENSIDAD
        # --------------------------------------------------------

        if (
            intensity_ratio is not None
            and intensity_target is not None
            and intensity_real is not None
            and intensity_type is not None
        ):

            intensity_difference = (
                self._percent_difference(
                    intensity_real,
                    intensity_target,
                )
            )

            if intensity_difference is not None:

                if abs(intensity_difference) <= 10:

                    feedback_parts.append(
                        f"{intensity_type.capitalize()} "
                        "bien ajustada al objetivo."
                    )

                elif intensity_difference < 0:

                    feedback_parts.append(
                        f"{intensity_type.capitalize()} "
                        f"{abs(intensity_difference):.1f}% "
                        "inferior al objetivo."
                    )

                else:

                    feedback_parts.append(
                        f"{intensity_type.capitalize()} "
                        f"{intensity_difference:.1f}% "
                        "superior al objetivo."
                    )

        # --------------------------------------------------------
        # DURACIÓN
        # --------------------------------------------------------

        if (
            real_duration is not None
            and target_duration is not None
            and target_duration > 0
        ):

            duration_difference = (
                self._percent_difference(
                    real_duration,
                    target_duration,
                )
            )

            if real_duration >= target_duration:

                feedback_parts.append(
                    "Duración completada."
                )

            elif real_duration >= (
                target_duration * 0.85
            ):

                feedback_parts.append(
                    "Duración casi completada."
                )

            elif real_duration >= (
                target_duration * 0.55
            ):

                feedback_parts.append(
                    "Sesión acortada."
                )

            else:

                feedback_parts.append(
                    "Duración muy inferior "
                    "a la prevista."
                )

        # --------------------------------------------------------
        # TSS
        # --------------------------------------------------------

        if (
            real_tss is not None
            and target_tss is not None
            and target_tss > 0
        ):

            tss_difference = self._percent_difference(
                real_tss,
                target_tss,
            )

            if tss_difference is not None:

                if abs(tss_difference) <= 10:

                    feedback_parts.append(
                        "Carga muy cercana al objetivo."
                    )

                elif tss_difference < 0:

                    feedback_parts.append(
                        f"Carga {abs(tss_difference):.1f}% "
                        "inferior a la prevista."
                    )

                else:

                    feedback_parts.append(
                        f"Carga {tss_difference:.1f}% "
                        "superior a la prevista."
                    )

        # --------------------------------------------------------
        # ESTADO
        # --------------------------------------------------------

        if (
            completion_ratio
            >= self.COMPLETE_THRESHOLD
        ):

            status = "COMPLETED"

        elif (
            completion_ratio
            >= self.PARTIAL_THRESHOLD
        ):

            status = "PARTIAL"

        else:

            status = "NOT_COMPLETED"

        # --------------------------------------------------------
        # MENSAJE PRINCIPAL
        # --------------------------------------------------------

        if status == "COMPLETED":

            feedback = (
                "🟢 Entrenamiento realizado correctamente."
            )

        elif status == "PARTIAL":

            feedback = (
                "🟡 Entrenamiento realizado parcialmente."
            )

        else:

            feedback = (
                "🔴 Entrenamiento realizado por "
                "debajo del objetivo."
            )

        if feedback_parts:

            feedback += (
                " "
                + " ".join(feedback_parts)
            )

        return WorkoutEvaluation(
            status=status,
            score=score,
            completion_percent=completion_percent,
            duration_real=real_duration,
            duration_target=target_duration,
            tss_real=real_tss,
            tss_target=target_tss,
            power_real=real_power,
            heart_rate_real=real_hr,
            feedback=feedback,
        )
