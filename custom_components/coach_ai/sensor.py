"""Sensores de Coach AI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import CoachAICoordinator
from .entity import CoachAIEntity


# ================================================================
# DESCRIPCIÓN DE SENSOR
# ================================================================


@dataclass(frozen=True, kw_only=True)
class CoachAISensorEntityDescription(
    SensorEntityDescription
):
    """Descripción de un sensor."""

    translation_key: str | None = None

    value_fn: Callable[
        [dict[str, Any]],
        Any,
    ]


# ================================================================
# SENSORES
# ================================================================


SENSORS: tuple[
    CoachAISensorEntityDescription,
    ...
] = (

    # ============================================================
    # DATOS DEL ATLETA
    # ============================================================

    CoachAISensorEntityDescription(
        key="body_battery",
        name="Body Battery",
        icon="mdi:battery-heart-variant",
        native_unit_of_measurement="%",
        value_fn=lambda data: (
            data["athlete"].body_battery
        ),
    ),

    CoachAISensorEntityDescription(
        key="sleep_score",
        name="Sleep Score",
        icon="mdi:sleep",
        native_unit_of_measurement="%",
        value_fn=lambda data: (
            data["athlete"].sleep_score
        ),
    ),

    CoachAISensorEntityDescription(
        key="training_readiness",
        name="Training Readiness",
        icon="mdi:run-fast",
        native_unit_of_measurement="%",
        value_fn=lambda data: (
            data["athlete"].training_readiness
        ),
    ),

    CoachAISensorEntityDescription(
        key="stress",
        name="Stress",
        icon="mdi:brain",
        value_fn=lambda data: (
            data["athlete"].stress
        ),
    ),

    CoachAISensorEntityDescription(
        key="hrv_status",
        name="HRV Status",
        icon="mdi:heart-pulse",
        value_fn=lambda data: (
            data["athlete"].hrv_status
        ),
    ),

    # ============================================================
    # ATHENA
    # ============================================================

    CoachAISensorEntityDescription(
        key="recovery_score",
        name="Recovery Score",
        icon="mdi:heart-pulse",
        native_unit_of_measurement="%",
        value_fn=lambda data: (
            data["athena"].recovery_score
        ),
    ),

    CoachAISensorEntityDescription(
        key="coach_score",
        name="Coach Score",
        icon="mdi:brain",
        native_unit_of_measurement="%",
        value_fn=lambda data: (
            data["athena"].coach_score
        ),
    ),

    CoachAISensorEntityDescription(
        key="fatigue",
        name="Fatigue",
        icon="mdi:battery-heart",
        value_fn=lambda data: (
            data["athena"].fatigue
        ),
    ),

    CoachAISensorEntityDescription(
        key="fitness",
        name="Fitness",
        icon="mdi:trophy",
        value_fn=lambda data: (
            data["athena"].fitness
        ),
    ),

    CoachAISensorEntityDescription(
        key="recommendation",
        name="Recommendation",
        icon="mdi:brain",
        value_fn=lambda data: (
            data["athena"].recommendation
        ),
    ),

    CoachAISensorEntityDescription(
        key="intelligence",
        name="Intelligence",
        icon="mdi:brain",
        value_fn=lambda data: (
            data["athena"].intelligence
        ),
    ),

    CoachAISensorEntityDescription(
        key="overtraining_risk",
        name="Overtraining Risk",
        icon="mdi:alert-octagon",
        value_fn=lambda data: (
            data["athena"].overtraining_risk
        ),
    ),

    CoachAISensorEntityDescription(
        key="overtraining_score",
        name="Overtraining Score",
        icon="mdi:alert",
        native_unit_of_measurement="%",
        value_fn=lambda data: (
            data["athena"].overtraining_score
        ),
    ),

    CoachAISensorEntityDescription(
        key="profile",
        name="Profile",
        icon="mdi:account",
        value_fn=lambda data: (
            data["athena"].profile
        ),
    ),

    CoachAISensorEntityDescription(
        key="load_status",
        name="Load Status",
        icon="mdi:chart-line",
        value_fn=lambda data: (
            data["athena"].load_status
        ),
    ),

    CoachAISensorEntityDescription(
        key="load_progression",
        name="Load Progression",
        icon="mdi:chart-timeline",
        value_fn=lambda data: (
            data["athena"].load_progression
        ),
    ),

    CoachAISensorEntityDescription(
        key="performance_score",
        name="Performance Score",
        icon="mdi:speedometer",
        native_unit_of_measurement="%",
        value_fn=lambda data: (
            data["athena"].performance_score
        ),
    ),

    CoachAISensorEntityDescription(
        key="load_score",
        name="Load Score",
        icon="mdi:gauge",
        native_unit_of_measurement="%",
        value_fn=lambda data: (
            data["athena"].load_score
        ),
    ),

    CoachAISensorEntityDescription(
        key="fatigue_trend",
        name="Fatigue Trend",
        icon="mdi:chart-timeline-variant",
        value_fn=lambda data: (
            data["athena"].fatigue_trend
        ),
    ),

    CoachAISensorEntityDescription(
        key="decision",
        name="Decision",
        icon="mdi:brain",
        value_fn=lambda data: (
            data["athena"].decision
        ),
    ),

    CoachAISensorEntityDescription(
        key="final_recommendation",
        name="Final Recommendation",
        icon="mdi:lightbulb-auto",
        value_fn=lambda data: (
            data["athena"].final_recommendation
        ),
    ),

    # ============================================================
    # SEMANA
    # ============================================================

    CoachAISensorEntityDescription(
        key="training_days",
        name="Training Days",
        icon="mdi:bike",
        value_fn=lambda data: len(
            [
                day
                for day in (
                    data["athena"].week or []
                )
                if str(
                    getattr(
                        day,
                        "workout",
                        "",
                    )
                ).lower()
                not in {
                    "rest",
                    "descanso",
                    "recovery",
                    "recuperación",
                    "recuperacion",
                }
            ]
        ),
    ),

    CoachAISensorEntityDescription(
        key="rest_days",
        name="Rest Days",
        icon="mdi:bed",
        value_fn=lambda data: len(
            [
                day
                for day in (
                    data["athena"].week or []
                )
                if str(
                    getattr(
                        day,
                        "workout",
                        "",
                    )
                ).lower()
                in {
                    "rest",
                    "descanso",
                }
            ]
        ),
    ),

    CoachAISensorEntityDescription(
        key="workout_score",
        name="Workout Score",
        icon="mdi:star-circle",
        native_unit_of_measurement="%",
        value_fn=lambda data: (
            data["athena"].workout_score
        ),
    ),

    CoachAISensorEntityDescription(
        key="workout_quality",
        name="Workout Quality",
        icon="mdi:medal",
        value_fn=lambda data: (
            data["athena"].workout_quality
        ),
    ),

    CoachAISensorEntityDescription(
        key="brain",
        name="Athena Brain",
        icon="mdi:brain",
        value_fn=lambda data: (
            data["athena"].brain
        ),
    ),

    # ============================================================
    # CARGA
    # ============================================================

    CoachAISensorEntityDescription(
        key="ctl",
        name="CTL",
        icon="mdi:chart-line",
        value_fn=lambda data: (
            data["athlete"].ctl
        ),
    ),

    CoachAISensorEntityDescription(
        key="atl",
        name="ATL",
        icon="mdi:chart-bell-curve",
        value_fn=lambda data: (
            data["athlete"].atl
        ),
    ),

    CoachAISensorEntityDescription(
        key="tsb",
        name="TSB",
        icon="mdi:scale-balance",
        value_fn=lambda data: (
            data["athlete"].tsb
        ),
    ),

    CoachAISensorEntityDescription(
        key="weekly_tss",
        name="Weekly TSS",
        icon="mdi:calendar-week",
        value_fn=lambda data: data.get(
            "weekly_tss",
            data["athlete"].weekly_tss,
        ),
    ),

    CoachAISensorEntityDescription(
        key="monthly_tss",
        name="Monthly TSS",
        icon="mdi:calendar-month",
        value_fn=lambda data: data.get(
            "monthly_tss",
            data["athlete"].monthly_tss,
        ),
    ),

    CoachAISensorEntityDescription(
        key="adaptive_workout",
        name="Adaptive Workout",
        icon="mdi:robot",
        value_fn=lambda data: (
            data["athena"].adaptive_workout
        ),
    ),

    CoachAISensorEntityDescription(
key="tomorrow_recovery",
        name="Tomorrow Recovery",
        icon="mdi:calendar-arrow-right",
        native_unit_of_measurement="%",
        value_fn=lambda data: (
            data["athena"].tomorrow_recovery
        ),
    ),

    CoachAISensorEntityDescription(
        key="readiness",
        name="Readiness",
        icon="mdi:run-fast",
        value_fn=lambda data: (
            data["athena"].readiness
        ),
    ),

    CoachAISensorEntityDescription(
        key="recovery_quality",
        name="Recovery Quality",
        icon="mdi:heart-plus",
        value_fn=lambda data: (
            data["athena"].recovery_quality
        ),
    ),

    CoachAISensorEntityDescription(
        key="confidence",
        name="AI Confidence",
        icon="mdi:shield-check",
        native_unit_of_measurement="%",
        value_fn=lambda data: (
            data["athena"].confidence
        ),
    ),

    CoachAISensorEntityDescription(
        key="experience",
        name="Experience",
        icon="mdi:brain",
        value_fn=lambda data: (
            data["athena"].experience
        ),
    ),

    CoachAISensorEntityDescription(
        key="experience_score",
        name="Experience Score",
        icon="mdi:school",
        native_unit_of_measurement="%",
        value_fn=lambda data: (
            data["athena"].experience_score
        ),
    ),

    CoachAISensorEntityDescription(
        key="consistency",
        name="Consistency",
        icon="mdi:calendar-check",
        value_fn=lambda data: (
            data["athena"].consistency
        ),
    ),

    CoachAISensorEntityDescription(
        key="consistency_score",
        name="Consistency Score",
        icon="mdi:chart-line",
        native_unit_of_measurement="%",
        value_fn=lambda data: (
            data["athena"].consistency_score
        ),
    ),

    # ============================================================
    # ENTRENAMIENTO PLANIFICADO
    # ============================================================

    CoachAISensorEntityDescription(
        key="workout",
        name="Workout",
        icon="mdi:bike",
        value_fn=lambda data: (
            data["athena"].training.workout
            if data["athena"].training
            else None
        ),
    ),

    CoachAISensorEntityDescription(
        key="duration",
        name="Workout Duration",
        icon="mdi:timer",
        native_unit_of_measurement="min",
        value_fn=lambda data: (
            data["athena"].training.duration
            if data["athena"].training
            else None
        ),
    ),

    CoachAISensorEntityDescription(
        key="zone",
        name="Training Zone",
        icon="mdi:speedometer",
        value_fn=lambda data: (
            data["athena"].training.zone
            if data["athena"].training
            else None
        ),
    ),

    CoachAISensorEntityDescription(
        key="target_power",
        name="Target Power",
        icon="mdi:flash",
        native_unit_of_measurement="W",
        value_fn=lambda data: (
            data["athena"].training.target_power
            if data["athena"].training
            else None
        ),
    ),

    CoachAISensorEntityDescription(
        key="target_hr",
        name="Target Heart Rate",
        icon="mdi:heart",
        native_unit_of_measurement="bpm",
        value_fn=lambda data: (
            data["athena"].training.target_hr
            if data["athena"].training
            else None
        ),
    ),

    CoachAISensorEntityDescription(
        key="cadence",
        name="Cadence",
        icon="mdi:rotate-right",
        native_unit_of_measurement="rpm",
        value_fn=lambda data: (
            data["athena"].training.cadence
            if data["athena"].training
            else None
        ),
    ),

    CoachAISensorEntityDescription(
        key="target_tss",
        name="Target TSS",
        icon="mdi:chart-line",
        value_fn=lambda data: (
            data["athena"].training.target_tss
            if data["athena"].training
            else None
        ),
    ),

    CoachAISensorEntityDescription(
        key="reason",
        name="Workout Reason",
        icon="mdi:text-box-outline",
        value_fn=lambda data: (
            data["athena"].training.reason
            if data["athena"].training
            else None
        ),
    ),

    # ============================================================
    # GARMIN — ÚLTIMA ACTIVIDAD
    # ============================================================

    CoachAISensorEntityDescription(
        key="last_activity",
        name="Last Activity",
        icon="mdi:bike",
        value_fn=lambda data: (
            getattr(
                data.get("last_activity"),
                "activity_name",
                None,
            )
        ),
    ),

    CoachAISensorEntityDescription(
        key="last_activity_duration",
        name="Last Activity Duration",
        icon="mdi:timer",
        native_unit_of_measurement="min",
        value_fn=lambda data: (
            getattr(
                data.get("last_activity"),
                "duration",
                None,
            )
        ),
    ),

    CoachAISensorEntityDescription(
        key="last_activity_tss",
        name="Last Activity TSS",
        icon="mdi:fire",
        value_fn=lambda data: (
            getattr(
                data.get("last_activity"),
                "training_load",
                None,
            )
        ),
    ),

    CoachAISensorEntityDescription(
        key="last_activity_power",
        name="Last Activity Power",
        icon="mdi:flash",
        native_unit_of_measurement="W",
        value_fn=lambda data: (
            getattr(
                data.get("last_activity"),
                "avg_power",
                None,
            )
        ),
    ),

    CoachAISensorEntityDescription(
        key="last_activity_hr",
        name="Last Activity Heart Rate",
        icon="mdi:heart-pulse",
        native_unit_of_measurement="bpm",
        value_fn=lambda data: (
            getattr(
                data.get("last_activity"),
                "avg_hr",
                None,
            )
        ),
    ),

    CoachAISensorEntityDescription(
        key="last_activity_vo2max",
        name="Last Activity VO2max",
        icon="mdi:lungs",
        value_fn=lambda data: (
            getattr(
                data.get("last_activity"),
                "vo2max",
                None,
            )
        ),
    ),

    CoachAISensorEntityDescription(
        key="last_activity_calories",
        name="Last Activity Calories",
        icon="mdi:fire",
        native_unit_of_measurement="kcal",
        value_fn=lambda data: (
            getattr(
                data.get("last_activity"),
                "calories",
                None,
            )
        ),
    ),

    # ============================================================
    # TEST FTP
    # ============================================================

    CoachAISensorEntityDescription(
        key="ftp_test_status", name="FTP Test Status", icon="mdi:flask-outline",
        value_fn=lambda data: data.get("ftp_test", {}).get("status"),
    ),
    CoachAISensorEntityDescription(
        key="ftp_test_power_20min", name="FTP Test 20min Power", icon="mdi:flash",
        native_unit_of_measurement="W",
        value_fn=lambda data: data.get("ftp_test", {}).get("power_20min"),
    ),
    CoachAISensorEntityDescription(
        key="ftp_test_estimated", name="FTP Test Estimated", icon="mdi:speedometer",
        native_unit_of_measurement="W",
        value_fn=lambda data: data.get("ftp_test", {}).get("ftp_95"),
    ),
    CoachAISensorEntityDescription(
        key="ftp_test_previous", name="FTP Test Previous FTP", icon="mdi:history",
        native_unit_of_measurement="W",
        value_fn=lambda data: data.get("ftp_test", {}).get("previous_ftp"),
    ),
    CoachAISensorEntityDescription(
        key="ftp_test_recommended", name="FTP Test Recommended", icon="mdi:target",
        native_unit_of_measurement="W",
        value_fn=lambda data: data.get("ftp_test", {}).get("ftp_recommended"),
    ),
    CoachAISensorEntityDescription(
        key="ftp_test_confidence", name="FTP Test Confidence", icon="mdi:shield-check",
        native_unit_of_measurement="%",
        value_fn=lambda data: data.get("ftp_test", {}).get("confidence"),
    ),
    CoachAISensorEntityDescription(
        key="ftp_test_coverage", name="FTP Test Coverage", icon="mdi:chart-donut",
        native_unit_of_measurement="%",
        value_fn=lambda data: data.get("ftp_test", {}).get("coverage_percent"),
    ),

    # ============================================================
    # EJECUCIÓN DEL ENTRENAMIENTO
    # ============================================================

    CoachAISensorEntityDescription(
        key="execution_status",
        name="Execution Status",
        icon="mdi:check-circle",
        value_fn=lambda data: (
            getattr(
                data.get("workout_evaluation"),
                "status",
                None,
            )
        ),
    ),

    CoachAISensorEntityDescription(
        key="execution_score",
        name="Execution Score",
        icon="mdi:star-circle",
        native_unit_of_measurement="/10",
        value_fn=lambda data: (
            getattr(
                data.get("workout_evaluation"),
                "score",
                None,
            )
        ),
    ),

    CoachAISensorEntityDescription(
        key="execution_completion",
        name="Execution Completion",
        icon="mdi:progress-check",
        native_unit_of_measurement="%",
        value_fn=lambda data: (
            getattr(
                data.get("workout_evaluation"),
                "completion_percent",
                None,
            )
        ),
    ),

    CoachAISensorEntityDescription(
        key="execution_feedback",
        name="Execution Feedback",
        icon="mdi:comment-text",
        value_fn=lambda data: (
            getattr(
                data.get("workout_evaluation"),
                "feedback",
                None,
            )
        ),
    ),
)


# ================================================================
# CONFIGURACIÓN
# ================================================================


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configura los sensores."""

    coordinator: CoachAICoordinator = (
        hass.data[DOMAIN][
            entry.entry_id
        ]
    )

    async_add_entities(
        [
            CoachAISensor(
                coordinator,
                description,
            )
            for description in SENSORS
        ]
    )


# ================================================================
# ENTIDAD
# ================================================================


class CoachAISensor(
    CoachAIEntity,
    SensorEntity,
):
    """Representa un sensor de Coach AI."""

    entity_description: (
        CoachAISensorEntityDescription
    )

    def __init__(
        self,
        coordinator: CoachAICoordinator,
        description: CoachAISensorEntityDescription,
    ) -> None:
        """Inicializa el sensor."""

        super().__init__(
            coordinator
        )

        self.entity_description = (
            description
        )

        self._attr_unique_id = (
            f"{DOMAIN}_{description.key}"
        )

        self._attr_has_entity_name = True

    # ============================================================
    # VALOR
    # ============================================================

    @property
    def native_value(self) -> Any:
        """Devuelve el valor del sensor."""

        if self.coordinator.data is None:
            return None

        try:

            return self.entity_description.value_fn(
                self.coordinator.data
            )

        except (
            AttributeError,
            KeyError,
            TypeError,
            ValueError,
        ):

            return None

    # ============================================================
    # DISPONIBILIDAD
    # ============================================================

    @property
    def available(self) -> bool:
        """Indica si está disponible."""

        return (
            super().available
            and self.coordinator.data is not None
        )

    # ============================================================
    # ATRIBUTOS
    # ============================================================

    @property
    def extra_state_attributes(
        self,
    ) -> dict[str, Any]:
        """Devuelve atributos adicionales."""

        if self.coordinator.data is None:
            return {}

        athlete = (
            self.coordinator.data[
                "athlete"
            ]
        )

        athena = (
            self.coordinator.data[
                "athena"
            ]
        )

        activity = (
            self.coordinator.data.get(
                "last_activity"
            )
        )

        evaluation = (
            self.coordinator.data.get(
                "workout_evaluation"
            )
        )

        attributes: dict[
            str,
            Any,
        ] = {}
        ftp_test = self.coordinator.data.get("ftp_test", {})
        if self.entity_description.key.startswith("ftp_test_"):
            attributes.update({
                "test_date": ftp_test.get("test_date"),
                "last_test_date": ftp_test.get("last_test_date"),
                "next_test_date": ftp_test.get("next_test_date"),
                "auto_scheduled": ftp_test.get("auto_scheduled", False),
                "validation_status": ftp_test.get("validation_status"),
                "athena_validation": ftp_test.get("athena_validation"),
                "ftp_auto_accepted": ftp_test.get("ftp_auto_accepted", False),
                "validation_pending": ftp_test.get("validation_pending", False),
                "message": ftp_test.get("message"),
                "ftp_intervals": ftp_test.get("ftp_intervals"),
                "uploaded": ftp_test.get("uploaded"),
                "scheduled": ftp_test.get("scheduled"),
                "fit_file": ftp_test.get("fit_file"),
                "coverage_percent": ftp_test.get("coverage_percent"),
                "power_source": ftp_test.get("power_source"),
                "power_std_percent": ftp_test.get("power_std_percent"),
                "split_difference_percent": ftp_test.get("split_difference_percent"),
                "intervals_entity": ftp_test.get("intervals_entity"),
                "activity_id": ftp_test.get("activity_id"),
                "analyzed_at": ftp_test.get("analyzed_at"),
            })


        # ========================================================
        # SLEEP
        # ========================================================

        if (
            self.entity_description.key
            == "sleep_score"
        ):

            attributes.update(
                {
                    "sleep_duration": (
                        athlete.sleep_duration
                    ),
                    "deep_sleep": (
                        athlete.deep_sleep
                    ),
                    "rem_sleep": (
                        athlete.rem_sleep
                    ),
                    "awake_duration": (
                        athlete.awake_duration
                    ),
                    "unmeasurable_sleep": (
                        athlete.unmeasurable_sleep
                    ),
                    "sleep_score_method": (
                        athlete.sleep_score_method
                    ),
                    "sleep_quality": (
                        athlete.sleep_quality
                    ),
                }
            )

        # ========================================================
        # CARGA
        # ========================================================

        if (
            self.entity_description.key
            == "ctl"
        ):

            attributes[
                "load_history"
            ] = self.coordinator.data.get(
                "load_history",
                [],
            )

        # ========================================================
        # RAZONES ATHENA
        # ========================================================

        if athena.reasons:

            attributes[
                "reasons"
            ] = athena.reasons

        # ========================================================
        # ENTRENAMIENTO
        # ========================================================

        if athena.training:

            training = (
                athena.training
            )

            attributes.update(
                {
                    "workout": (
                        training.workout
                    ),
                    "duration": (
                        training.duration
                    ),
                    "zone": (
                        training.zone
                    ),
                    "target_power": (
                        training.target_power
                    ),
                    "target_hr": (
                        training.target_hr
                    ),
                    "cadence": (
                        training.cadence
                    ),
                    "target_tss": (
                        training.target_tss
                    ),
                    "intensity_factor": (
                        training.intensity_factor
                    ),
                    "outdoor": (
                        training.outdoor
                    ),
                    "reason": (
                        training.reason
                    ),
                }
            )

            # ----------------------------------------------------
            # INTERVALOS
            # ----------------------------------------------------

            if training.intervals:

                attributes[
                    "intervals"
                ] = [
                    {
                        "name": getattr(
                            interval,
                            "name",
                            None,
                        ),
                        "duration": getattr(
                            interval,
                            "duration",
                            None,
                        ),
                        "power": getattr(
                            interval,
                            "power",
                            None,
                        ),
                        "heart_rate": getattr(
                            interval,
                            "heart_rate",
                            None,
                        ),
                        "cadence": getattr(
                            interval,
                            "cadence",
                            None,
                        ),
                    }
                    for interval
                    in training.intervals
                ]

        # ========================================================
        # PLAN SEMANAL
        # ========================================================

        if athena.week:

            attributes[
                "weekly_plan"
            ] = [
                {
                    "workout": getattr(
                        training,
                        "workout",
                        None,
                    ),
                    "duration": getattr(
                        training,
                        "duration",
                        None,
                    ),
                    "zone": getattr(
                        training,
                        "zone",
                        None,
                    ),
                    "target_tss": getattr(
                        training,
                        "target_tss",
                        None,
                    ),
                    "reason": getattr(
                        training,
                        "reason",
                        None,
                    ),
                }
                for training
                in athena.week
            ]

        # ========================================================
        # EJECUCIÓN SEMANAL
        # ========================================================

        weekly_execution = (
            self.coordinator.data.get(
                "weekly_execution",
                [],
            )
        )

        if weekly_execution:

            attributes[
                "weekly_execution"
            ] = weekly_execution

        # ========================================================
        # ARCHIVOS FIT
        # ========================================================

        if athena.weekly_files:

            attributes[
                "weekly_files"
            ] = athena.weekly_files

        # ========================================================
        # GARMIN
        # ========================================================

        if activity is not None:

            attributes.update(
                {
                    "activity_id": (
                        activity.activity_id
                    ),
                    "activity_name": (
                        activity.activity_name
                    ),
                    "activity_type": (
                        activity.activity_type
                    ),
                    "distance_km": (
                        activity.distance_km
                    ),
                    "duration": (
                        activity.duration
                    ),
                    "elapsed_duration": (
                        activity.elapsed_duration
                    ),
                    "moving_duration": (
                        activity.moving_duration
                    ),
                    "average_speed": (
                        activity.avg_speed
                    ),
                    "max_speed": (
                        activity.max_speed
                    ),
                    "average_hr": (
                        activity.avg_hr
                    ),
                    "max_hr": (
                        activity.max_hr
                    ),
                    "average_power": (
                        activity.avg_power
                    ),
                    "max_power": (
                        activity.max_power
                    ),
                    "normalized_power": (
                        activity.normalized_power
                    ),
                    "calories": (
                        activity.calories
                    ),
                    "training_load": (
                        activity.training_load
                    ),
                    "aerobic_training_effect": (
                        activity.aerobic_training_effect
                    ),
                    "anaerobic_training_effect": (
                        activity.anaerobic_training_effect
                    ),
                    "vo2max": (
                        activity.vo2max
                    ),
                    "training_effect_label": (
                        activity.training_effect_label
                    ),
                    "start_time": (
                        activity.start_time
                    ),
                    "moderate_intensity_minutes": (
                        activity.moderate_intensity_minutes
                    ),
                    "vigorous_intensity_minutes": (
                        activity.vigorous_intensity_minutes
                    ),
                }
            )

        # ========================================================
        # EVALUACIÓN
        # ========================================================

        if evaluation is not None:

            attributes.update(
                {
                    "execution_status": (
                        evaluation.status
                    ),
                    "execution_score": (
                        evaluation.score
                    ),
                    "execution_completion": (
                        evaluation.completion_percent
                    ),
                    "execution_duration_real": (
                        evaluation.duration_real
                    ),
                    "execution_duration_target": (
                        evaluation.duration_target
                    ),
                    "execution_tss_real": (
                        evaluation.tss_real
                    ),
                    "execution_tss_target": (
                        evaluation.tss_target
                    ),
                    "execution_power_real": (
                        evaluation.power_real
),
                    "execution_heart_rate_real": (
                        evaluation.heart_rate_real
                    ),
                    "execution_feedback": (
                        evaluation.feedback
                    ),
                }
            )

        # ========================================================
        # RESUMEN DE EJECUCIÓN
        # ========================================================

        if evaluation is not None:

            status = (
                evaluation.status
            )

            if status == "COMPLETED":

                execution_label = (
                    "🟢 REALIZADA"
                )

            elif status == "PARTIAL":

                execution_label = (
                    "🟡 PARCIAL"
                )

            else:

                execution_label = (
                    "🔴 NO REALIZADA"
                )

            attributes[
                "execution_label"
            ] = execution_label

        return attributes