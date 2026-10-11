"""Modelos de datos de Coach AI."""

from __future__ import annotations

from dataclasses import dataclass, field

from .goal import GoalType


@dataclass(slots=True)
class Interval:
    """Intervalo de entrenamiento."""

    name: str

    duration: int

    power: int | None = None

    heart_rate: int | None = None

    cadence: int | None = None

    step_type: str = "interval"

    intensity: str = "active"


@dataclass(slots=True)
class TrainingPlan:
    """Plan de entrenamiento."""

    workout: str

    duration: int

    zone: str

    target_power: int | None

    target_hr: int | None

    cadence: int | None

    target_tss: int

    intensity_factor: float | None

    outdoor: bool

    reason: str

    intervals: list[Interval] = field(
        default_factory=list
    )

    export: dict = field(
        default_factory=dict
    )


@dataclass(slots=True)
class ActivitySummary:
    """Resumen de una actividad real de Garmin."""

    activity_id: int | None = None

    activity_name: str | None = None

    activity_type: str | None = None

    distance_km: float | None = None

    duration: int | None = None

    elapsed_duration: int | None = None

    moving_duration: int | None = None

    avg_speed: float | None = None

    max_speed: float | None = None

    avg_hr: int | None = None

    max_hr: int | None = None

    avg_power: int | None = None

    max_power: int | None = None

    normalized_power: int | None = None

    calories: int | None = None

    training_load: float | None = None

    aerobic_training_effect: float | None = None

    anaerobic_training_effect: float | None = None

    vo2max: int | None = None

    training_effect_label: str | None = None

    start_time: str | None = None

    moderate_intensity_minutes: int | None = None

    vigorous_intensity_minutes: int | None = None


@dataclass(slots=True)
class NutritionPlan:
    """Plan nutricional."""

    carbs: int = 0

    protein: int = 0

    hydration: int = 0

    calories: int = 0


@dataclass(slots=True)
class AthleteState:
    """Estado actual del atleta."""

    # -------------------------------------------------
    # RECUPERACIÓN Y SALUD
    # -------------------------------------------------

    body_battery: int | None = None

    sleep_score: int | None = None

    sleep_duration: float | None = None

    deep_sleep: float | None = None

    rem_sleep: float | None = None

    awake_duration: float | None = None

    unmeasurable_sleep: float | None = None

    sleep_score_method: str | None = None

    sleep_quality: str | None = None

    training_readiness: int | None = None

    hrv_status: str | None = None

    stress: int | None = None

    resting_hr: int | None = None

    max_hr: int | None = None

    vo2max: int | None = None

    # -------------------------------------------------
    # DATOS FÍSICOS
    # -------------------------------------------------

    ftp: int | None = None

    weight: float | None = None

    age: int | None = None

    # -------------------------------------------------
    # CARGA DE ENTRENAMIENTO
    # -------------------------------------------------

    ctl: float | None = None

    atl: float | None = None

    tsb: float | None = None

    weekly_tss: int | None = None

    monthly_tss: int | None = None

    # -------------------------------------------------
    # METEOROLOGÍA
    # -------------------------------------------------

    temperature: float | None = None

    humidity: float | None = None

    wind_speed: float | None = None

    raining: bool = False

    # -------------------------------------------------
    # DISPONIBILIDAD
    # -------------------------------------------------

    available_minutes: int | None = None

    # -------------------------------------------------
    # COMPETICIÓN
    # -------------------------------------------------

    next_race: str | None = None

    days_to_race: int | None = None

    # -------------------------------------------------
    # OBJETIVO
    # -------------------------------------------------

    goal: GoalType = GoalType.MAINTENANCE


@dataclass(slots=True)
class AthenaResult:
    """Resultado completo del motor Athena."""

    # -------------------------------------------------
    # ESTADO PRINCIPAL
    # -------------------------------------------------

    recovery_score: int

    coach_score: int

    fatigue: str

    fatigue_score: int

    fitness: str

    recommendation: str

    # -------------------------------------------------
    # RIESGO
    # -------------------------------------------------

    overtraining_risk: str = "low"

    overtraining_score: int = 0

    # -------------------------------------------------
    # RESUMEN
    # -------------------------------------------------

    summary: str = ""

    adaptive_workout: str = ""

    tomorrow_recovery: int = 0

    # -------------------------------------------------
    # PERFIL E INTELIGENCIA
    # -------------------------------------------------

    profile: str = ""

    intelligence: str = ""

    # -------------------------------------------------
    # CARGA
    # -------------------------------------------------

    load_status: str = ""

    load_progression: str = ""

    load_score: int = 0

    # -------------------------------------------------
    # READINESS
    # -------------------------------------------------

    readiness: str = ""

    confidence: int = 0

    # -------------------------------------------------
    # EXPERIENCIA
    # -------------------------------------------------

    experience: str = ""

    experience_score: int = 0

    # -------------------------------------------------
    # DECISIÓN
    # -------------------------------------------------

    decision: str = ""

    performance_score: int = 0

    brain: str = ""

    # -------------------------------------------------
    # FATIGA
    # -------------------------------------------------

    fatigue_trend: str = ""

    recovery_quality: str = ""

    final_recommendation: str = ""

    # -------------------------------------------------
    # CONSISTENCIA
    # -------------------------------------------------

    consistency: str = ""

    consistency_score: int = 0

    # -------------------------------------------------
    # ENTRENAMIENTO
    # -------------------------------------------------

    workout_score: int = 0

    workout_quality: str = ""

    # -------------------------------------------------
    # OBJETIVO
    # -------------------------------------------------

    goal: object | None = None

    # -------------------------------------------------
    # INTELIGENCIA / APRENDIZAJE
    # -------------------------------------------------

    learning: dict = field(
        default_factory=dict
    )

    export: dict = field(
        default_factory=dict
    )

    insights: list[str] = field(
        default_factory=list
    )

    reasons: list[str] = field(
        default_factory=list
    )

    # -------------------------------------------------
    # PLANES
    # -------------------------------------------------

    training: TrainingPlan | None = None

    nutrition: NutritionPlan | None = None

    week: list[TrainingPlan] = field(
        default_factory=list
    )

    # -------------------------------------------------
    # ARCHIVOS
    # -------------------------------------------------

    weekly_files: list[str] = field(
        default_factory=list
    )