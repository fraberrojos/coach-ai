"""Motor principal de Coach AI."""

from __future__ import annotations

import logging

from homeassistant.util import dt as dt_util

from .fitness import FitnessEngine
from .models import AthleteState
from .models import AthenaResult
from .planner import PlannerEngine
from .recovery import RecoveryEngine
from .trend import TrendEngine
from .fatigue import FatigueEngine
from .insights import InsightEngine
from .predictor import PredictorEngine
from .intelligence import IntelligenceEngine
from .profile import ProfileEngine
from .load_analysis import LoadEngine
from .performance import PerformanceEngine
from .adaptive import AdaptivePlanner
from .forecast import ForecastEngine
from .load_score import LoadScoreEngine
from .fatigue_trend import FatigueTrendEngine
from .readiness import ReadinessEngine
from .recovery_quality import RecoveryQualityEngine
from .confidence import ConfidenceEngine
from .decision import DecisionEngine
from .optimizer import OptimizerEngine
from .interval_builder import IntervalBuilder
from .experience import ExperienceEngine
from .recommendation import RecommendationEngine
from .learning import LearningEngine
from .consistency import ConsistencyEngine
from .workout_evaluator import WorkoutEvaluator
from .adaptive_week import AdaptiveWeekEngine
from .brain import BrainEngine
from .goal import GoalEngine
from .workout_generator import WorkoutGenerator
from .workout_context import WorkoutContext
from .training_load import TrainingLoadEngine
from .workout_scaler import WorkoutScaler
from .workout_exporter import WorkoutExporter
from .garmin_builder import GarminBuilder
from .fit_builder import FitBuilder
from .workout_scheduler import WorkoutScheduler


_LOGGER = logging.getLogger(__name__)


class Athena:
    """Motor principal de decisión."""

    def __init__(self) -> None:
        """Inicializa los motores."""

        self.recovery_engine = RecoveryEngine()
        self.trend_engine = TrendEngine()
        self.planner_engine = PlannerEngine()
        self.fitness_engine = FitnessEngine()
        self.fatigue_engine = FatigueEngine()
        self.insight_engine = InsightEngine()
        self.predictor_engine = PredictorEngine()
        self.intelligence_engine = IntelligenceEngine()
        self.profile_engine = ProfileEngine()
        self.load_engine = LoadEngine()
        self.training_load_engine = TrainingLoadEngine()
        self.performance_engine = PerformanceEngine()
        self.adaptive_planner = AdaptivePlanner()
        self.forecast_engine = ForecastEngine()
        self.load_score_engine = LoadScoreEngine()
        self.fatigue_trend_engine = FatigueTrendEngine()
        self.readiness_engine = ReadinessEngine()
        self.recovery_quality_engine = RecoveryQualityEngine()
        self.confidence_engine = ConfidenceEngine()
        self.decision_engine = DecisionEngine()
        self.optimizer_engine = OptimizerEngine()
        self.interval_builder = IntervalBuilder()
        self.experience_engine = ExperienceEngine()
        self.recommendation_engine = RecommendationEngine()
        self.learning_engine = LearningEngine()
        self.consistency_engine = ConsistencyEngine()
        self.workout_evaluator = WorkoutEvaluator()
        self.adaptive_week_engine = AdaptiveWeekEngine()
        self.brain_engine = BrainEngine()
        self.goal_engine = GoalEngine()
        self.workout_generator = WorkoutGenerator()
        self.workout_scaler = WorkoutScaler()
        self.workout_exporter = WorkoutExporter()
        self.garmin_builder = GarminBuilder()
        self.fit_builder = FitBuilder()
        self.scheduler = WorkoutScheduler()

    @staticmethod
    def _build_execution_feedback(
        history: list[dict],
        limit: int = 3,
    ) -> list[dict]:
        """Extrae las últimas evaluaciones Garmin válidas para adaptar la semana."""
        if not history:
            return []

        feedback: list[dict] = []
        seen_ids: set[str] = set()

        for record in reversed(history):
            if not isinstance(record, dict):
                continue
            if record.get("type") != "athena_analysis":
                continue

            execution = record.get("execution")
            if not isinstance(execution, dict):
                continue

            activity_id = execution.get("activity_id")
            if activity_id is None:
                continue

            activity_key = str(activity_id)
            if activity_key in seen_ids:
                continue

            status = str(
                execution.get("status")
                or record.get("status")
                or ""
            ).upper()

            if status not in {"COMPLETED", "PARTIAL", "NOT_COMPLETED"}:
                continue

            completion = execution.get("completion_percent")
            try:
                completion = float(completion)
            except (TypeError, ValueError):
                continue

            feedback.append(
                {
                    "activity_id": activity_id,
                    "date": record.get("date"),
                    "workout": (
                        record.get("training", {})
                        if isinstance(record.get("training"), dict)
                        else {}
                    ).get("workout"),
                    "status": status,
                    "completion_percent": completion,
                    "score": execution.get("score"),
                    "duration_real": execution.get("duration_real"),
                    "tss_real": execution.get("tss_real"),
                    "power_real": execution.get("power_real"),
                    "feedback": execution.get("feedback"),
                }
            )
            seen_ids.add(activity_key)

            if len(feedback) >= limit:
                break

        return feedback

    def analyse(
        self,
        athlete: AthleteState,
        history: list[dict] | None = None,
        unavailable_days: set[int] | list[int] | None = None,
        requested_rest_days: set[int] | list[int] | None = None,
        requested_training_days: set[int] | list[int] | None = None,
    ) -> AthenaResult:
        """Analiza el estado del deportista.

        unavailable_days utiliza índices de 0 a 6:

        0 = lunes
        1 = martes
        2 = miércoles
        3 = jueves
        4 = viernes
        5 = sábado
        6 = domingo
        """

        if history is None:
            history = []

        # ---------------------------------------------------------
        # Normalizar días no disponibles
        # ---------------------------------------------------------

        blocked_days = {
            int(day)
            for day in (unavailable_days or [])
            if isinstance(day, int) and 0 <= int(day) <= 6
        }

        requested_rest_days = {
            int(day)
            for day in (requested_rest_days or [])
            if isinstance(day, int) and 0 <= int(day) <= 6
        }

        # Unavailable siempre prevalece sobre un descanso solicitado.
        requested_rest_days -= blocked_days

        requested_training_days = {
            int(day)
            for day in (requested_training_days or [])
            if isinstance(day, int) and 0 <= int(day) <= 6
        }
        requested_training_days -= blocked_days
        requested_training_days -= requested_rest_days

        # ---------------------------------------------------------
        # 1. Tendencia histórica
        # ---------------------------------------------------------

        trend = self.trend_engine.analyse(history)

        # ---------------------------------------------------------
        # 2. Score base de recuperación
        # ---------------------------------------------------------

        # =========================================================
        # DEBUG RECOVERY - ENTRADA REAL A ATHENA
        # =========================================================

        _LOGGER.debug(
            "Coach AI RECOVERY INPUT | "
            "BodyBattery=%s | "
            "Sleep=%s | "
            "Stress=%s | "
            "HRV=%s | "
            "TrainingReadiness=%s | "
            "CTL=%s | "
            "ATL=%s | "
            "TSB=%s | "
            "History=%s",
            athlete.body_battery,
            athlete.sleep_score,
            athlete.stress,
            athlete.hrv_status,
            athlete.training_readiness,
            athlete.ctl,
            athlete.atl,
            athlete.tsb,
            len(history),
        )

        recovery_score, reasons = self.recovery_engine.calculate(
            body_battery=athlete.body_battery,
            sleep_score=athlete.sleep_score,
            stress=athlete.stress,
            hrv_status=athlete.hrv_status,
            training_readiness=athlete.training_readiness,
            ctl=athlete.ctl,
            atl=athlete.atl,
            tsb=athlete.tsb,
        )

        # =========================================================
        # DEBUG RECOVERY - RESULTADO DEL RECOVERY ENGINE
        # =========================================================

        _LOGGER.debug(
            "Coach AI RECOVERY ENGINE RESULT | "
            "score=%s | reasons=%s",
            recovery_score,
            reasons,
        )

        recovery_quality = self.recovery_quality_engine.classify(
            recovery_score,
        )

        learning = self.learning_engine.analyse(history)

        consistency_score, consistency = (
            self.consistency_engine.analyse(history)
        )

        goal_profile = self.goal_engine.get_goal(
            athlete.goal,
        )

        # ---------------------------------------------------------
        # 3. Ajuste por tendencia
        # ---------------------------------------------------------

        if trend.recovery_trend == "declining":

            recovery_score -= 5

            reasons.append(
                "La recuperación está empeorando."
            )

        elif trend.recovery_trend == "improving":

            recovery_score += 3

            reasons.append(
                "La recuperación mejora respecto a días anteriores."
            )

        recovery_score = max(
            0,
            min(100, recovery_score),
        )

        # =========================================================
        # DEBUG RECOVERY - RESULTADO FINAL TRAS TENDENCIA
        # =========================================================

        _LOGGER.debug(
            "Coach AI RECOVERY FINAL | "
            "score=%s | "
            "trend=%s | "
            "reasons=%s",
            recovery_score,
            trend.recovery_trend,
            reasons,
        )

        # ---------------------------------------------------------
        # 4. Fatiga y recomendación
        # ---------------------------------------------------------

        if recovery_score >= 80:

            fatigue = "Baja"
            recommendation = "Entrenamiento intenso"

        elif recovery_score >= 60:

            fatigue = "Media"
            recommendation = "Entrenamiento normal"

        elif recovery_score >= 40:

            fatigue = "Alta"
            recommendation = "Recuperación activa"

        else:

            fatigue = "Muy alta"
            recommendation = "Descanso"

        # ---------------------------------------------------------
        # 5. Fitness
        # ---------------------------------------------------------

        fitness = self.fitness_engine.estimate(
            athlete.ctl or 0,
            athlete.atl or 0,
            athlete.tsb or 0,
        )

        fitness_score = {
            "detrained": 20,
            "building": 45,
            "fit": 70,
            "race_ready": 95,
            "overreached": 30,
        }.get(
            fitness,
            50,
        )

        # ---------------------------------------------------------
        # 6. Fatigue score
        # ---------------------------------------------------------

        fatigue_score = self.fatigue_engine.estimate(
            athlete.ctl,
            athlete.atl,
            athlete.tsb,
        )

        # ---------------------------------------------------------
        # 7. Coach Score
        # ---------------------------------------------------------

        coach_score = int(
            recovery_score * 0.7
            + fitness_score * 0.3
        )

        # ---------------------------------------------------------
        # 8. Riesgo
        # ---------------------------------------------------------

        risk, risk_score = self.predictor_engine.risk(
            athlete.ctl,
            athlete.atl,
            athlete.tsb,
            recovery_score,
        )

        readiness = self.readiness_engine.calculate(
            recovery_score,
            fatigue,
            risk,
        )

        confidence = self.confidence_engine.calculate(
            recovery_score,
            len(history),
            athlete.hrv_status,
            athlete.sleep_score,
        )

        experience_score, experience = (
            self.experience_engine.analyse(history)
        )

        decision = self.decision_engine.decide(
            readiness,
            risk,
            confidence,
        )

        # ---------------------------------------------------------
        # 9. Contexto de entrenamiento
        # ---------------------------------------------------------

        context = WorkoutContext(
            recovery=recovery_score,
            readiness=readiness,
            fatigue=fatigue,
            fitness=fitness,
            goal=goal_profile.goal,
            available_minutes=athlete.available_minutes or 90,
            ctl=athlete.ctl or 0,
            atl=athlete.atl or 0,
            tsb=athlete.tsb or 0,
            confidence=confidence,
            ftp=athlete.ftp,
            consistency=consistency_score,
            experience=experience,
        )

        # ---------------------------------------------------------
        # 10. Entrenamiento del día
        #
        # El entrenamiento definitivo se selecciona DESPUÉS de
        # construir y adaptar la semana. Así, un día no disponible
        # no puede mantener un entrenamiento independiente.
        # ---------------------------------------------------------

        training = None

        # ---------------------------------------------------------
        # 11. Insights
        # ---------------------------------------------------------

        insights = self.insight_engine.build(
            recovery_score,
            fitness,
            fatigue,
            recommendation,
        )

        # ---------------------------------------------------------
        # 12. PLAN SEMANAL
        # ---------------------------------------------------------

        week_plan = self.scheduler.build_week(
            athlete,
            context,
            unavailable_days=blocked_days,
        )

        if week_plan is None:
            week_plan = []

        # ---------------------------------------------------------
        # 13. ADAPTACIÓN INTELIGENTE DE LA SEMANA
        # ---------------------------------------------------------

        execution_feedback = self._build_execution_feedback(history)

        _LOGGER.debug(
            "Coach AI ADAPTIVE FEEDBACK | sesiones=%s",
            execution_feedback,
        )

        week_plan = self.adaptive_week_engine.optimise(
            week_plan,
            recovery_score,
            consistency_score,
            risk,
            context.tsb,
            context.atl,
            unavailable_days=blocked_days,
            requested_rest_days=requested_rest_days,
            requested_training_days=requested_training_days,
            execution_feedback=execution_feedback,
            current_day_index=dt_util.now().weekday(),
        )

        # ---------------------------------------------------------
        # 13.1 SINCRONIZACIÓN FINAL DEL ENTRENAMIENTO
        # ---------------------------------------------------------

        def _sync_training(training_plan):
            if training_plan is None:
                return training_plan
            if training_plan.workout in {"Rest", "Unavailable"}:
                return training_plan
            if not athlete.ftp:
                return training_plan

            duration = max(1, int(training_plan.duration or 1))
            try:
                if str(training_plan.workout).strip().lower() in {
                    "recovery", "recuperación", "recuperacion",
                }:
                    from .models import Interval
                    target_power = round(float(athlete.ftp) * 0.45)
                    training_plan.intervals = [Interval(
                        name="Recovery", duration=duration, power=target_power,
                        heart_rate=None, cadence=90, step_type="recovery",
                        intensity="rest",
                    )]
                    training_plan.target_power = target_power
                    return training_plan

                rebuilt = self.interval_builder.build(
                    training_plan.workout, duration, recovery_score, 1.0, ftp=athlete.ftp
                )
                if rebuilt:
                    training_plan.intervals = rebuilt
                    powers = [int(i.power) for i in rebuilt if i.power is not None]
                    if powers:
                        training_plan.target_power = max(powers)
            except Exception:
                _LOGGER.exception("Coach AI: error sincronizando entrenamiento %s", training_plan.workout)
            return training_plan

        for index, planned_training in enumerate(week_plan):
            if planned_training is not None:
                week_plan[index] = _sync_training(planned_training)

        # ---------------------------------------------------------
        # 13.1 ENTRENAMIENTO DEFINITIVO DE HOY
        #
        # La semana adaptada es la única fuente de verdad para
        # el entrenamiento que se muestra como "hoy".
        # ---------------------------------------------------------

        today_index = dt_util.now().weekday()

        if 0 <= today_index < len(week_plan):
            training = week_plan[today_index]

            # -----------------------------------------------------
            # INVARIANTE FINAL: la sesión de hoy manda.
            # Su duración e intervalos deben ser idénticos.
            # -----------------------------------------------------
            training = _sync_training(training)

            if training is not None and training.workout not in {"Rest", "Unavailable"}:
                duration = max(1, int(training.duration or 1))

                if str(training.workout).strip().lower() in {
                    "recovery", "recuperación", "recuperacion",
                } and athlete.ftp:
                    from .models import Interval
                    target_power = round(float(athlete.ftp) * 0.45)
                    training.intervals = [
                        Interval(
                            name="Recovery",
                            duration=duration,
                            power=target_power,
                            heart_rate=None,
                            cadence=90,
                            step_type="recovery",
                            intensity="rest",
                        )
                    ]
                    training.target_power = target_power
                elif athlete.ftp:
                    training.intervals = self.interval_builder.build(
                        training.workout,
                        duration,
                        recovery_score,
                        1.0,
                        ftp=athlete.ftp,
                    )
                    powers = [
                        int(i.power) for i in training.intervals
                        if i.power is not None
                    ]
                    if powers:
                        training.target_power = max(powers)

                # La entrada del week_plan de hoy debe ser exactamente
                # la misma sesión que se muestra como entrenamiento actual.
                week_plan[today_index] = training

            if training is not None:
                training.export = self.workout_exporter.export_json(training)

                _LOGGER.info(
                    "Coach AI TODAY TRAINING FINAL | day=%s | workout=%s | "
                    "duration=%s | target_power=%s | intervals=%s | interval_total=%s",
                    today_index,
                    training.workout,
                    training.duration,
                    training.target_power,
                    len(training.intervals),
                    sum(int(i.duration) for i in training.intervals),
                )
        else:
            _LOGGER.debug(
                "Coach AI: week_plan no contiene el día actual "
                "(%s). Se mantiene entrenamiento vacío.",
                today_index,
            )

        # ---------------------------------------------------------
        # 14. Exportación FIT semanal
        # ---------------------------------------------------------

        # Athena genera el plan y sus datos de exportación.
        # La escritura del FIT se gestiona fuera de Athena para evitar
        # generar el mismo entrenamiento varias veces.
        weekly_files = []

        # ---------------------------------------------------------
        # 15. Intelligence
        # ---------------------------------------------------------

        intelligence = self.intelligence_engine.analyse(
            recovery_score,
            coach_score,
            fitness,
            fatigue,
            risk,
        )

        # ---------------------------------------------------------
        # 16. Load
        # ---------------------------------------------------------

        load = self.load_engine.analyse(
            athlete.ctl,
            athlete.atl,
            athlete.tsb,
        )

        load_score = self.load_score_engine.calculate(
            athlete.ctl,
            athlete.atl,
            athlete.tsb,
        )

        # ---------------------------------------------------------
        # 17. Performance
        # ---------------------------------------------------------

        performance_score = self.performance_engine.score(
            athlete.ctl,
            recovery_score,
            fitness,
            risk,
        )

        # ---------------------------------------------------------
        # 18. Brain
        # ---------------------------------------------------------

        brain = self.brain_engine.think(
            recovery_score,
            fitness,
            fatigue,
            readiness,
            risk,
            confidence,
            consistency_score,
            performance_score,
        )

        # ---------------------------------------------------------
        # 19. Perfil
        # ---------------------------------------------------------

        profile = self.profile_engine.classify(
            athlete,
        )

        adaptive_workout = self.adaptive_planner.choose(
            athlete,
            recovery_score,
            performance_score,
            risk,
            profile,
        )

        # ---------------------------------------------------------
        # 20. Previsión
        # ---------------------------------------------------------

        tomorrow_recovery = self.forecast_engine.tomorrow(
            recovery_score,
            fatigue,
            risk,
        )

        fatigue_trend = self.fatigue_trend_engine.analyse(
            history,
        )

        # ---------------------------------------------------------
        # 21. Recomendación final
        # ---------------------------------------------------------

        final_recommendation = self.recommendation_engine.build(
            decision,
            recovery_score,
            confidence,
        )

        workout_score, workout_quality = (
            self.workout_evaluator.evaluate(
                training,
            )
        )

        # ---------------------------------------------------------
        # 22. Resumen
        # ---------------------------------------------------------

        summary = (
            f"{recommendation}. "
            f"Objetivo: {goal_profile.name}. "
            f"Recovery {recovery_score}%. "
            f"Performance {performance_score}%. "
            f"Fitness {fitness}. "
            f"Fatiga {fatigue}. "
            f"Sesión recomendada: {adaptive_workout}."
        )

        # ---------------------------------------------------------
        # 23. Resultado Athena
        # ---------------------------------------------------------

        return AthenaResult(
            recovery_score=recovery_score,
            coach_score=coach_score,
            fatigue=fatigue,
            fatigue_score=fatigue_score,
            fitness=fitness,
            recommendation=recommendation,
            reasons=reasons,
            training=training,
            week=week_plan,
            weekly_files=weekly_files,
            summary=summary,
            insights=insights,
            overtraining_risk=risk,
            overtraining_score=risk_score,
            intelligence=intelligence,
            profile=profile,
            load_status=load["status"],
            load_progression=load["progression"],
            performance_score=performance_score,
            adaptive_workout=adaptive_workout,
            tomorrow_recovery=tomorrow_recovery,
            load_score=load_score,
            fatigue_trend=fatigue_trend,
            readiness=readiness,
            recovery_quality=recovery_quality,
            confidence=confidence,
            decision=decision,
            experience=experience,
            experience_score=experience_score,
            final_recommendation=final_recommendation,
            learning=learning,
            consistency=consistency,
            consistency_score=consistency_score,
            workout_score=workout_score,
            workout_quality=workout_quality,
            brain=brain,
            export={},
        )