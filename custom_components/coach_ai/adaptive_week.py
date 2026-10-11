"""Motor de adaptación semanal de Coach AI."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .models import Interval
from .models import TrainingPlan


class AdaptiveWeekEngine:
    """Adapta la semana automáticamente según el estado del atleta."""

    HARD_WORKOUTS = {
        "Sweet Spot",
        "Threshold",
        "VO2 Max",
        "Tempo",
    }

    WORKOUT_PRIORITY = {
        "Threshold": 100,
        "Sweet Spot": 95,
        "VO2 Max": 90,
        "Long Ride": 85,
        "Tempo": 80,
        "Endurance": 70,
        "Recovery": 40,
        "Rest": 0,
        "Unavailable": -100,
    }

    def optimise(
        self,
        week: list[TrainingPlan],
        recovery: int,
        consistency: int,
        risk: str,
        tsb: float | None = None,
        atl: float | None = None,
        unavailable_days: set[int] | list[int] | None = None,
        requested_rest_days: set[int] | list[int] | None = None,
        requested_training_days: set[int] | list[int] | None = None,
        execution_feedback: list[dict[str, Any]] | None = None,
        current_day_index: int | None = None,
    ) -> list[TrainingPlan]:
        """Adapta la planificación semanal."""

        if not week:
            return []

        # =========================================================
        # NORMALIZACIÓN
        # =========================================================

        week = list(week[:7])

        while len(week) < 7:
            week.append(
                self._create_rest(
                    "Descanso añadido por Athena."
                )
            )

        # =========================================================
        # VALORES SEGUROS
        # =========================================================

        current_recovery = max(
            0,
            min(100, int(recovery)),
        )

        current_consistency = max(
            0,
            min(100, int(consistency)),
        )

        current_tsb = (
            float(tsb)
            if tsb is not None
            else 0.0
        )

        current_atl = (
            float(atl)
            if atl is not None
            else 0.0
        )

        _ = current_atl

        # =========================================================
        # DISPONIBILIDAD
        # =========================================================

        blocked_days = {
            int(day)
            for day in (unavailable_days or [])
            if isinstance(day, int)
            and 0 <= int(day) <= 6
        }
        requested_rest_days = {
            int(day)
            for day in (requested_rest_days or [])
            if isinstance(day, int)
            and 0 <= int(day) <= 6
        } - blocked_days
        requested_training_days = {
            int(day)
            for day in (requested_training_days or [])
            if isinstance(day, int)
            and 0 <= int(day) <= 6
        } - blocked_days - requested_rest_days

        protected_days = blocked_days | requested_rest_days | requested_training_days

        if blocked_days:
            week = self._apply_unavailable_days(
                week,
                blocked_days,
            )

        if requested_rest_days:
            week = self._apply_requested_rest_days(
                week,
                requested_rest_days,
                blocked_days | requested_rest_days,
            )

        if requested_training_days:
            week = self._apply_requested_training_days(
                week,
                requested_training_days,
                blocked_days | requested_rest_days,
            )

        # =========================================================
        # RIESGO CRÍTICO
        # =========================================================

        if risk == "critical":

            for index, day in enumerate(week):

                if index in protected_days:
                    continue

                if day.workout in self.HARD_WORKOUTS:

                    self._make_rest(
                        day,
                        "Descanso impuesto por riesgo crítico.",
                    )

                elif day.workout == "Long Ride":

                    self._reduce_session(
                        day,
                        duration_factor=0.60,
                        tss_factor=0.60,
                        power_factor=0.90,
                        reason=(
                            "Long Ride reducido por "
                            "riesgo crítico."
                        ),
                    )

                elif day.workout == "Endurance":

                    self._reduce_session(
                        day,
                        duration_factor=0.75,
                        tss_factor=0.75,
                        power_factor=0.95,
                        reason=(
                            "Endurance reducido por "
                            "riesgo crítico."
                        ),
                    )

            self._apply_execution_feedback(
                week,
                execution_feedback or [],
                protected_days,
                current_day_index,
            )

            self._ensure_recovery_distribution(
                week,
                protected_days,
            )

            return week

        # =========================================================
        # TSB MUY NEGATIVO
        # =========================================================

        if current_tsb < -25:

            converted = False

            for index, day in enumerate(week):

                if index in protected_days:
                    continue

                if day.workout in self.HARD_WORKOUTS:

                    self._make_rest(
                        day,
                        "Descanso añadido por TSB muy negativo.",
                    )

                    converted = True
                    break

            if not converted:

                for index, day in enumerate(week):

                    if index in protected_days:
                        continue

                    if day.workout == "Long Ride":

                        self._reduce_session(
                            day,
                            duration_factor=0.75,
                            tss_factor=0.75,
                            power_factor=0.95,
                            reason=(
                                "Volumen reducido por "
                                "TSB muy negativo."
                            ),
                        )

                        break

        # =========================================================
        # TSB MODERADAMENTE NEGATIVO
        # =========================================================

        elif current_tsb < -15:

            for index, day in enumerate(week):

                if index in protected_days:
                    continue

                if day.workout in {
                    "Threshold",
                    "VO2 Max",
                }:

                    self._reduce_session(
                        day,
                        duration_factor=0.80,
                        tss_factor=0.80,
                        power_factor=0.95,
                        reason=(
                            "Intensidad reducida por "
                            "carga acumulada."
                        ),
                    )

                elif day.workout == "Long Ride":

                    self._reduce_session(
                        day,
                        duration_factor=0.85,
                        tss_factor=0.85,
                        power_factor=0.95,
                        reason=(
                            "Volumen reducido por "
                            "carga acumulada."
                        ),
                    )

        # =========================================================
        # RECUPERACIÓN MUY BAJA
        # =========================================================

        if current_recovery < 25:

            hard_converted = False

            for index, day in enumerate(week):

                if index in protected_days:
                    continue

                if day.workout in self.HARD_WORKOUTS:

                    self._convert_to_recovery(
                        day,
                        (
                            "Sesión intensa sustituida por "
                            "recuperación muy baja."
                        ),
                    )

                    hard_converted = True
                    break

            for index, day in enumerate(week):

                if index in protected_days:
                    continue

                if day.workout in {
                    "Rest",
                    "Recovery",
                }:
                    continue

                self._reduce_session(
                    day,
                    duration_factor=0.85,
                    tss_factor=0.85,
                    power_factor=0.95,
                    reason=(
                        "Volumen reducido por "
                        "recuperación muy baja."
                    ),
                )

        # =========================================================
        # RECUPERACIÓN BAJA
        # =========================================================

        elif current_recovery < 40:

            for index, day in enumerate(week):

                if index in protected_days:
                    continue

                if day.workout in self.HARD_WORKOUTS:

                    self._convert_to_recovery(
                        day,
                        (
                            "Sesión intensa sustituida por "
                            "recuperación baja."
                        ),
                    )

                    break

            for index, day in enumerate(week):

                if index in protected_days:
                    continue

                if day.workout in {
                    "Rest",
                    "Recovery",
                }:
                    continue

                self._reduce_session(
                    day,
                    duration_factor=0.85,
                    tss_factor=0.85,
                    power_factor=0.95,
                    reason=(
                        "Volumen adaptado por "
                        "recuperación baja."
                    ),
                )

        # =========================================================
        # RECUPERACIÓN MEDIA
        # =========================================================

        elif current_recovery < 60:

            for index, day in enumerate(week):

                if index in protected_days:
                    continue

                if day.workout in {
                    "Threshold",
                    "VO2 Max",
                }:

                    self._reduce_session(
                        day,
                        duration_factor=0.90,
                        tss_factor=0.90,
                        power_factor=0.97,
                        reason=(
                            "Intensidad moderada por "
                            "recuperación media."
                        ),
                    )

        # =========================================================
        # SEPARAR SESIONES DURAS
        # =========================================================

        self._separate_hard_sessions(
            week,
            protected_days,
        )

        # =========================================================
        # BUENA RECUPERACIÓN
        # =========================================================

        if (
            current_recovery > 80
            and current_consistency > 80
            and current_tsb > -10
        ):

            for index, day in enumerate(week):

                if index in protected_days:
                    continue

                if day.workout in {
                    "Endurance",
                    "Long Ride",
                }:

                    self._increase_volume(
                        day,
                        factor=1.10,
                        reason=(
                            "Volumen aumentado por buena "
                            "recuperación y consistencia."
                        ),
                    )

        # =========================================================
        # ADAPTACIÓN SEGÚN EJECUCIÓN REAL DE GARMIN
        # =========================================================

        self._apply_execution_feedback(
            week,
            execution_feedback or [],
            protected_days,
            current_day_index,
        )

        # =========================================================
        # GARANTIZAR DESCANSO
        # =========================================================

        self._ensure_recovery_distribution(
            week,
            protected_days,
        )

        return week

    # =============================================================
    # ADAPTACIÓN SEGÚN EJECUCIÓN REAL
    # =============================================================

    def _apply_execution_feedback(
        self,
        week: list[TrainingPlan],
        feedback: list[dict[str, Any]],
        protected_days: set[int],
        current_day_index: int | None,
    ) -> None:
        """Adapta sesiones futuras usando las últimas ejecuciones reales.

        La adaptación es deliberadamente conservadora: una sesión parcial
        aislada reduce ligeramente la siguiente sesión disponible; varias
        sesiones claramente incompletas provocan una reducción mayor. Las
        sesiones ya pasadas y el día actual no se modifican por este motor.
        """
        if not feedback or not week:
            return

        # Solo analizamos resultados recientes con actividad real.
        usable: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        for item in feedback:
            if not isinstance(item, dict):
                continue

            activity_id = item.get("activity_id")
            if activity_id is None:
                continue

            activity_key = str(activity_id)
            if activity_key in seen_ids:
                continue

            status = str(item.get("status") or "").upper()
            if status not in {"COMPLETED", "PARTIAL", "NOT_COMPLETED"}:
                continue

            try:
                completion = float(item.get("completion_percent"))
            except (TypeError, ValueError):
                continue

            completion = max(0.0, min(100.0, completion))
            usable.append({"status": status, "completion": completion})
            seen_ids.add(activity_key)

            if len(usable) >= 3:
                break

        if not usable:
            return

        latest = usable[0]
        partials = sum(
            1
            for item in usable
            if item["status"] in {"PARTIAL", "NOT_COMPLETED"}
        )

        # Una sesión completada no genera compensación.
        if latest["status"] == "COMPLETED" and latest["completion"] >= 85:
            return

        # Determinamos la magnitud de la adaptación.
        if latest["status"] == "NOT_COMPLETED" or latest["completion"] < 55:
            duration_factor = 0.80
            tss_factor = 0.80
            power_factor = 0.93
            reason = (
                "Carga futura reducida por entrenamiento no completado "
                "o cumplimiento muy bajo según Garmin."
            )
        elif partials >= 2:
            duration_factor = 0.85
            tss_factor = 0.85
            power_factor = 0.95
            reason = (
                "Carga futura reducida por varias sesiones parciales "
                "detectadas en Garmin."
            )
        elif latest["completion"] < 80:
            duration_factor = 0.90
            tss_factor = 0.90
            power_factor = 0.95
            reason = (
                "Siguiente sesión ajustada por cumplimiento parcial "
                "del entrenamiento anterior."
            )
        else:
            duration_factor = 0.95
            tss_factor = 0.95
            power_factor = 0.97
            reason = (
                "Siguiente sesión ligeramente ajustada por cumplimiento "
                "parcial del entrenamiento anterior."
            )

        start_index = 0 if current_day_index is None else max(0, current_day_index + 1)
        candidate_indexes = [
            index
            for index, day in enumerate(week)
            if index >= start_index
            and index not in protected_days
            and day.workout not in {"Rest", "Unavailable", "Recovery"}
        ]

        if not candidate_indexes:
            return

        # Priorizamos la próxima sesión real, no una sesión lejana.
        candidate = candidate_indexes[0]
        day = week[candidate]

        self._reduce_session(
            day,
            duration_factor=duration_factor,
            tss_factor=tss_factor,
            power_factor=power_factor,
            reason=reason,
        )

    # =============================================================
    # PREFERENCIAS DEL USUARIO
    # =============================================================

    def _apply_requested_rest_days(
        self,
        week: list[TrainingPlan],
        requested_days: set[int],
        protected_days: set[int],
    ) -> list[TrainingPlan]:
        """Protege los días elegidos por el usuario como descanso."""
        sessions_to_move: list[tuple[int, TrainingPlan]] = []

        for index in sorted(requested_days):
            if index >= len(week):
                continue
            day = week[index]
            if day.workout == "Rest":
                day.reason = self._append_reason(day.reason, "🛌 Descanso solicitado por el usuario.")
                continue
            if day.workout == "Unavailable":
                continue
            sessions_to_move.append((index, deepcopy(day)))
            self._make_rest(day, "🛌 Descanso solicitado por el usuario.")

        available_days = [
            index for index, day in enumerate(week)
            if index not in protected_days and day.workout == "Rest"
        ]
        sessions_to_move.sort(
            key=lambda item: self.WORKOUT_PRIORITY.get(item[1].workout, 50),
            reverse=True,
        )
        for original_index, session in sessions_to_move:
            destination = self._find_best_destination(week, available_days, session)
            if destination is None:
                week[original_index].reason = self._append_reason(
                    week[original_index].reason,
                    "⚠️ Descanso solicitado, pero la sesión no se pudo recolocar por falta de un día libre seguro.",
                )
                continue
            session.reason = self._append_reason(
                session.reason,
                f"Sesión trasladada al {self._day_name(destination)} por descanso solicitado.",
            )
            week[destination] = session
            available_days.remove(destination)
        return week

    def _apply_requested_training_days(
        self,
        week: list[TrainingPlan],
        requested_days: set[int],
        protected_days: set[int],
    ) -> list[TrainingPlan]:
        """Intenta garantizar una sesión en los días elegidos por el usuario."""
        for index in sorted(requested_days):
            if index >= len(week):
                continue
            day = week[index]
            if day.workout not in {"Rest", "Unavailable"}:
                day.reason = self._append_reason(day.reason, "🚴 Entrenamiento solicitado por el usuario.")
                continue

            candidates = [
                i for i, candidate in enumerate(week)
                if i not in protected_days
                and i not in requested_days
                and candidate.workout not in {"Rest", "Unavailable"}
            ]
            if not candidates:
                day.reason = self._append_reason(
                    day.reason,
                    "⚠️ Entrenamiento solicitado, pero no hay otra sesión segura que trasladar.",
                )
                continue

            # Preferimos mover una sesión de menor prioridad antes que desplazar una sesión clave.
            source = min(
                candidates,
                key=lambda i: self.WORKOUT_PRIORITY.get(week[i].workout, 50),
            )
            session = deepcopy(week[source])
            self._make_rest(
                week[source],
                "Sesión trasladada por entrenamiento solicitado.",
            )
            session.reason = self._append_reason(
                session.reason,
                f"Sesión trasladada al {self._day_name(index)} por entrenamiento solicitado.",
            )
            week[index] = session
        return week

    # =============================================================
    # DISPONIBILIDAD
    # =============================================================

    def _apply_unavailable_days(
        self,
        week: list[TrainingPlan],
        blocked_days: set[int],
    ) -> list[TrainingPlan]:
        """Recoloca las sesiones de los días bloqueados."""

        sessions_to_move: list[
            tuple[int, TrainingPlan]
        ] = []

        # ---------------------------------------------------------
        # Guardamos las sesiones originales.
        # ---------------------------------------------------------

        for index in sorted(blocked_days):

            if index >= len(week):
                continue

            day = week[index]

            if day.workout in {
                "Rest",
                "Unavailable",
            }:
                continue

            sessions_to_move.append(
                (
                    index,
                    deepcopy(day),
                )
            )

            self._make_unavailable(
                day,
            )

        if not sessions_to_move:
            return week

        # ---------------------------------------------------------
        # Días libres reales.
        # ---------------------------------------------------------

        available_days = [
            index
            for index, day in enumerate(week)
            if (
                index not in blocked_days
                and day.workout == "Rest"
            )
        ]

        # ---------------------------------------------------------
        # Primero las sesiones más importantes.
        # ---------------------------------------------------------

        sessions_to_move.sort(
            key=lambda item: self.WORKOUT_PRIORITY.get(
                item[1].workout,
                50,
            ),
            reverse=True,
        )

        for original_index, session in sessions_to_move:

            destination = self._find_best_destination(
                week,
                available_days,
                session,
            )

            if destination is None:

                week[original_index].reason = (
                    "🚫 Día no disponible. "
                    "Sesión cancelada por falta de "
                    "un día disponible seguro."
                )

                continue

            session.reason = self._append_reason(
                session.reason,
                (
                    f"Sesión trasladada al "
                    f"{self._day_name(destination)} "
                    "por indisponibilidad."
                ),
            )

            week[destination] = session

            available_days.remove(destination)

        return week

    # =============================================================
    # BUSCAR DESTINO
    # =============================================================

    def _find_best_destination(
        self,
        week: list[TrainingPlan],
        candidates: list[int],
        session: TrainingPlan,
    ) -> int | None:
        """Busca el mejor día para recolocar una sesión."""

        if not candidates:
            return None

        scored: list[tuple[int, int]] = []

        for candidate in candidates:

            score = 0

            # -----------------------------------------------------
            # Separar sesiones duras.
            # -----------------------------------------------------

            if session.workout in self.HARD_WORKOUTS:

                previous_index = candidate - 1
                next_index = candidate + 1

                if previous_index >= 0:

                    if (
                        week[previous_index].workout
                        in self.HARD_WORKOUTS
                    ):
                        score -= 100

                if next_index < len(week):

                    if (
                        week[next_index].workout
                        in self.HARD_WORKOUTS
                    ):
                        score -= 100

            # -----------------------------------------------------
            # Preferimos descanso alrededor.
            # -----------------------------------------------------

            if candidate > 0:

                if week[candidate - 1].workout == "Rest":
                    score += 20

            if candidate < len(week) - 1:

                if week[candidate + 1].workout == "Rest":
                    score += 20

            # -----------------------------------------------------
            # Long Ride preferentemente fin de semana.
            # -----------------------------------------------------

            if session.workout == "Long Ride":

                if candidate >= 4:
                    score += 25

            # -----------------------------------------------------
            # Entrenamientos de calidad.
            # -----------------------------------------------------

            elif session.workout in {
                "Threshold",
                "Sweet Spot",
                "VO2 Max",
                "Tempo",
            }:

                if candidate in {
                    1,
                    2,
                    4,
                }:
                    score += 10

            scored.append(
                (
                    score,
                    candidate,
                )
            )

        scored.sort(
            key=lambda item: (
                item[0],
                -item[1],
            ),
            reverse=True,
        )

        return scored[0][1]

    # =============================================================
    # SEPARAR SESIONES DURAS
    # =============================================================

    def _separate_hard_sessions(
        self,
        week: list[TrainingPlan],
        blocked_days: set[int],
    ) -> None:
        """Evita sesiones duras consecutivas."""

        for index in range(len(week) - 1):

            if index in blocked_days:
                continue

            next_index = index + 1

            if next_index in blocked_days:
                continue

            current = week[index]
            next_day = week[next_index]

            if (
                current.workout in self.HARD_WORKOUTS
                and next_day.workout in self.HARD_WORKOUTS
            ):

                # Conservamos la sesión más importante.
                current_priority = self.WORKOUT_PRIORITY.get(
                    current.workout,
                    50,
                )

                next_priority = self.WORKOUT_PRIORITY.get(
                    next_day.workout,
                    50,
                )

                if current_priority >= next_priority:

                    target = next_day

                else:

                    target = current

                self._reduce_session(
                    target,
                    duration_factor=0.75,
                    tss_factor=0.75,
                    power_factor=0.90,
                    reason=(
                        "Carga reducida para evitar "
                        "sesiones intensas consecutivas."
                    ),
                )

    # =============================================================
    # REDUCIR
    # =============================================================

    @staticmethod
    def _reduce_session(
        day: TrainingPlan,
        duration_factor: float,
        tss_factor: float,
        power_factor: float,
        reason: str,
    ) -> None:
        """Reduce una sesión manteniendo sus intervalos."""

        if day.workout in {
            "Rest",
            "Unavailable",
        }:
            return

        original_duration = day.duration

        day.duration = max(
            20,
            int(
                original_duration
                * duration_factor
            ),
        )

        day.target_tss = max(
            1,
            int(
                day.target_tss
                * tss_factor
            ),
        )

        if day.target_power is not None:

            day.target_power = round(
                day.target_power
                * power_factor
            )

        if day.intensity_factor is not None:

            day.intensity_factor = round(
                day.intensity_factor
                * power_factor,
                3,
            )

        AdaptiveWeekEngine._scale_intervals(
            day,
            day.duration,
            power_factor,
        )

        day.reason = AdaptiveWeekEngine._append_reason(
            day.reason,
            reason,
        )

    # =============================================================
    # AUMENTAR VOLUMEN
    # =============================================================

    @staticmethod
    def _increase_volume(
        day: TrainingPlan,
        factor: float,
        reason: str,
    ) -> None:
        """Aumenta el volumen de una sesión."""

        if day.workout in {
            "Rest",
            "Unavailable",
            "Recovery",
        }:
            return

        day.duration = int(
            day.duration * factor
        )

        day.target_tss = int(
            day.target_tss * factor
        )

        AdaptiveWeekEngine._scale_intervals(
            day,
            day.duration,
            1.0,
        )

        day.reason = AdaptiveWeekEngine._append_reason(
            day.reason,
            reason,
        )

    # =============================================================
    # ESCALAR INTERVALOS
    # =============================================================

    @staticmethod
    def _scale_intervals(
        day: TrainingPlan,
        target_duration: int,
        power_factor: float,
    ) -> None:
        """Escala los intervalos para coincidir con la sesión."""

        if not day.intervals:
            return

        original_total = sum(
            interval.duration
            for interval in day.intervals
        )

        if original_total <= 0:
            return

        ratio = (
            target_duration
            / original_total
        )

        new_durations: list[int] = []

        for interval in day.intervals:

            new_durations.append(
                max(
                    1,
                    round(
                        interval.duration
                        * ratio
                    ),
                )
            )

        difference = (
            target_duration
            - sum(new_durations)
        )

        if new_durations:
            new_durations[-1] = max(
                1,
                new_durations[-1]
                + difference,
            )

        for index, interval in enumerate(
            day.intervals
        ):

            interval.duration = (
                new_durations[index]
            )

            if interval.power is not None:

                interval.power = round(
                    interval.power
                    * power_factor
                )

    # =============================================================
    # CONVERTIR A RECOVERY
    # =============================================================

    @staticmethod
    def _convert_to_recovery(
        day: TrainingPlan,
        reason: str,
    ) -> None:
        """Convierte una sesión en recuperación."""

        day.workout = "Recovery"
        day.duration = 40
        day.zone = "Z1"

        day.target_power = (
            round(
                day.target_power * 0.45
            )
            if day.target_power is not None
            else None
        )

        day.target_hr = 110
        day.cadence = 90
        day.target_tss = 20
        day.intensity_factor = 0.45
        day.outdoor = False

        day.intervals = [
            Interval(
                name="Recovery",
                duration=40,
                power=day.target_power,
                heart_rate=110,
                cadence=90,
                step_type="recovery",
                intensity="rest",
            )
        ]

        day.reason = AdaptiveWeekEngine._append_reason(
            day.reason,
            reason,
        )

    # =============================================================
    # DESCANSO
    # =============================================================

    @staticmethod
    def _make_rest(
        day: TrainingPlan,
        reason: str,
    ) -> None:
        """Convierte una sesión en descanso real."""

        day.workout = "Rest"
        day.duration = 0
        day.zone = "REST"
        day.target_power = None
        day.target_hr = None
        day.cadence = None
        day.target_tss = 0
        day.intensity_factor = 0.0
        day.outdoor = False
        day.intervals = []

        day.reason = AdaptiveWeekEngine._append_reason(
            day.reason,
            reason,
        )

    @staticmethod
    def _create_rest(
        reason: str,
    ) -> TrainingPlan:
        """Crea un descanso real."""

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
    def _make_unavailable(
        day: TrainingPlan,
    ) -> None:
        """Marca un día como no disponible."""

        day.workout = "Unavailable"
        day.duration = 0
        day.zone = "REST"
        day.target_power = None
        day.target_hr = None
        day.cadence = None
        day.target_tss = 0
        day.intensity_factor = 0.0
        day.outdoor = False
        day.intervals = []

        day.reason = (
            "🚫 Día no disponible."
        )

    # =============================================================
    # DISTRIBUCIÓN DE DESCANSO
    # =============================================================

    def _ensure_recovery_distribution(
        self,
        week: list[TrainingPlan],
        blocked_days: set[int],
    ) -> None:
        """Garantiza al menos un descanso real."""

        available = [
            index
            for index in range(len(week))
            if index not in blocked_days
        ]

        if not available:
            return

        rest_days = [
            index
            for index in available
            if week[index].workout == "Rest"
        ]

        # Dos descansos ya son suficientes.
        if len(rest_days) >= 2:
            return

        # Si no hay descanso, creamos uno.
        if not rest_days:

            candidates = [
                index
                for index in available
                if week[index].workout
                not in {
                    "Rest",
                    "Recovery",
                }
            ]

            if not candidates:
                return

            candidate = min(
                candidates,
                key=lambda index: self.WORKOUT_PRIORITY.get(
                    week[index].workout,
                    50,
                ),
            )

            self._make_rest(
                week[candidate],
                (
                    "Descanso añadido para equilibrar "
                    "la carga semanal."
                ),
            )

    # =============================================================
    # UTILIDADES
    # =============================================================

    @staticmethod
    def _append_reason(
        current: str | None,
        addition: str,
    ) -> str:
        """Añade una explicación."""

        if current:
            return f"{current} | {addition}"

        return addition

    @staticmethod
    def _day_name(
        index: int,
    ) -> str:
        """Devuelve el nombre del día."""

        names = (
            "lunes",
            "martes",
            "miércoles",
            "jueves",
            "viernes",
            "sábado",
            "domingo",
        )

        if 0 <= index < len(names):
            return names[index]

        return f"día {index + 1}"