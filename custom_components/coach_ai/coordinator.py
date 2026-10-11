"""Coordinator principal de Coach AI."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import hashlib
import json
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .activity import ActivityEngine
from .athena import Athena
from .builder import AthleteBuilder
from .history import HistoryManager
from .load import LoadEngine
from .ftp_test import FTPTestEngine
from .garmin_mcp_client import (
    GarminMCPClient,
    GarminMCPError,
    build_garmin_cycling_workout,
    extract_records,
)
from .models import Interval, TrainingPlan
from .notifier import CoachAINotifier
from .workout_evaluator import WorkoutEvaluator
from .workout_exporter import WorkoutExporter


_LOGGER = logging.getLogger(__name__)


class CoachAICoordinator(
    DataUpdateCoordinator[dict[str, Any]]
):
    """Coordinator principal de Coach AI."""

    # ============================================================
    # DÍAS DE LA SEMANA
    # ============================================================

    UNAVAILABLE_DAY_ENTITIES = {
        0: "input_boolean.coach_ai_unavailable_monday",
        1: "input_boolean.coach_ai_unavailable_tuesday",
        2: "input_boolean.coach_ai_unavailable_wednesday",
        3: "input_boolean.coach_ai_unavailable_thursday",
        4: "input_boolean.coach_ai_unavailable_friday",
        5: "input_boolean.coach_ai_unavailable_saturday",
        6: "input_boolean.coach_ai_unavailable_sunday",
    }

    DAY_PREFERENCE_ENTITIES = {
        0: "input_select.coach_ai_day_monday",
        1: "input_select.coach_ai_day_tuesday",
        2: "input_select.coach_ai_day_wednesday",
        3: "input_select.coach_ai_day_thursday",
        4: "input_select.coach_ai_day_friday",
        5: "input_select.coach_ai_day_saturday",
        6: "input_select.coach_ai_day_sunday",
    }

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Inicializa el coordinator."""

        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name="Coach AI",
            update_interval=timedelta(
                minutes=15
            ),
        )

        self.hass = hass

        self.builder = AthleteBuilder(hass)
        self.history = HistoryManager(hass)
        self.load_engine = LoadEngine()
        self.ftp_test = FTPTestEngine()
        self.athena = Athena()
        self.notifier = CoachAINotifier(hass)
        self.workout_exporter = WorkoutExporter()

        # --------------------------------------------------------
        # Garmin / ejecución real
        # --------------------------------------------------------

        self.activity_engine = ActivityEngine(hass)
        self.workout_evaluator = WorkoutEvaluator()

        self._last_signature: tuple | None = None
        self._force_recalculate: bool = False
        self._last_garmin_sync_signature: tuple | None = None
        # Evita que una caída del Garmin Bridge bloquee/reintente la sincronización
        # en cada actualización de Athena. Tras el enfriamiento se vuelve a intentar.
        self._garmin_sync_blocked_until: datetime | None = None

        # --------------------------------------------------------
        # Test FTP
        # --------------------------------------------------------
        self._ftp_test_loaded: bool = False
        self._ftp_test_auto_running: bool = False
        self._ftp_test_result: dict[str, Any] = {
            "status": "not_started",
            "power_20min": None,
            "ftp_95": None,
            "previous_ftp": None,
            "ftp_intervals": None,
            "ftp_recommended": None,
            "confidence": None,
            "message": "Todavía no se ha realizado ningún test FTP.",
            "test_date": None,
            "last_test_date": None,
            "next_test_date": None,
            "auto_scheduled": False,
            "validation_status": "not_started",
            "athena_validation": None,
            "ftp_auto_accepted": False,
        }

    # ============================================================
    # DÍAS NO DISPONIBLES
    # ============================================================

    def _get_unavailable_days(self) -> set[int]:
        """Obtiene los días que el atleta no puede entrenar."""

        unavailable_days: set[int] = set()

        for day_index, entity_id in (
            self.UNAVAILABLE_DAY_ENTITIES.items()
        ):
            state = self.hass.states.get(
                entity_id
            )

            if state is None:
                continue

            if state.state == "on":
                unavailable_days.add(
                    day_index
                )

        return unavailable_days

    def _get_day_preferences(self) -> tuple[set[int], set[int], set[int], dict[int, str]]:
        """Lee la preferencia de los siete días."""
        unavailable: set[int] = set()
        rest: set[int] = set()
        training: set[int] = set()
        preferences: dict[int, str] = {}

        for day_index, entity_id in self.DAY_PREFERENCE_ENTITIES.items():
            state = self.hass.states.get(entity_id)
            value = state.state if state is not None else "Athena"
            preferences[day_index] = value
            normalized = value.strip().lower()
            if normalized == "no disponible":
                unavailable.add(day_index)
            elif normalized == "descanso":
                rest.add(day_index)
            elif normalized == "entrenamiento":
                training.add(day_index)

        # Mantener compatibilidad con los antiguos helpers de no disponibilidad.
        unavailable |= self._get_unavailable_days()
        rest -= unavailable
        training -= unavailable | rest
        return unavailable, rest, training, preferences

    # ============================================================
    # CONTROL DEL PLAN DIARIO
    # ============================================================

    async def async_recalculate_week(self) -> None:
        """Fuerza un nuevo cálculo de la semana y del día actual."""
        self._force_recalculate = True
        await self.async_request_refresh()

    async def async_start_ftp_test(
        self,
        test_date: date | None = None,
        automatic: bool = False,
    ) -> dict[str, Any]:
        """Genera el test FTP y lo programa en Garmin.

        Si no se indica fecha, se programa para mañana. ``automatic``
        identifica el ciclo automático de 6 semanas.
        """
        athlete = self.builder.build()
        previous_ftp = getattr(athlete, "ftp", None)
        training = self.ftp_test.generate(previous_ftp=previous_ftp)

        # Generamos también el FIT local para mantener el mismo flujo de
        # exportación que el resto de entrenamientos de Coach AI.
        fit_file = None
        try:
            fit_file = self.workout_exporter.save_fit(training)
        except Exception:
            _LOGGER.exception("Coach AI FTP: error generando FIT del test.")

        # Garmin necesita una fecha futura para que el test quede programado
        # de forma explícita y no interfiera con el entrenamiento de hoy.
        if test_date is None:
            test_date = dt_util.now().date() + timedelta(days=1)

        synced, uploaded, scheduled = await self._sync_training_to_garmin(
            training,
            test_date,
        )

        result = {
            "status": "scheduled" if synced else "generated",
            "workout": training.workout,
            "duration": training.duration,
            "test_date": test_date.isoformat(),
            "previous_ftp": previous_ftp,
            "fit_file": fit_file,
            "uploaded": uploaded,
            "scheduled": scheduled,
            "power_20min": None,
            "ftp_95": None,
            "ftp_intervals": None,
            "ftp_recommended": None,
            "confidence": None,
            "message": (
                "Test programado. Pendiente de realizar y analizar la actividad Garmin."
                if synced
                else "Test generado. Pendiente de programarlo o realizarlo manualmente."
            ),
            "last_test_date": self._ftp_test_result.get("last_test_date"),
            "next_test_date": (
                (test_date + timedelta(days=42)).isoformat()
                if synced
                else self._ftp_test_result.get("next_test_date")
            ),
            "auto_scheduled": automatic,
        }

        self._ftp_test_result = result
        await self._persist_ftp_test_result()
        self.async_update_listeners()

        if synced:
            await self.notifier.send(
                "🧪 Coach AI · Test FTP",
                (
                    "Test FTP de 20 min preparado.\n"
                    f"Programado para: {test_date.isoformat()}\n"
                    "Duración: 60 min\n"
                    f"FTP actual de referencia: {previous_ftp or 'N/D'} W\n"
                    "El bloque de 20 min es OPEN.\n"
                    "El FTP no se modificará automáticamente."
                ),
                data={
                    "actions": [
                        {
                            "action": "URI",
                            "title": "📥 Descargar FIT",
                            "uri": "/local/coach_ai/ftp_test_-_20_min.fit",
                        }
                    ]
                },
            )
        else:
            await self.notifier.send(
                "⚠️ Coach AI · Test FTP",
                (
                    "El test FTP se ha generado localmente, pero no se pudo "
                    "programar automáticamente en Garmin.\n"
                    f"Fecha prevista: {test_date.isoformat()}"
                ),
            )

        return result

    async def async_register_manual_ftp_result(
        self,
        power_20min: float,
        ftp_95: float | None = None,
        previous_ftp: float | None = None,
    ) -> dict[str, Any]:
        """Registra manualmente un resultado FTP pendiente de validacion."""
        try:
            power = float(power_20min)
        except (TypeError, ValueError):
            raise ValueError("power_20min debe ser numerico") from None
        if power <= 0:
            raise ValueError("power_20min debe ser mayor que 0")

        if ftp_95 is None:
            ftp_value = round(power * 0.95, 1)
        else:
            try:
                ftp_value = float(ftp_95)
            except (TypeError, ValueError):
                raise ValueError("ftp_95 debe ser numerico") from None
            if ftp_value <= 0:
                raise ValueError("ftp_95 debe ser mayor que 0")

        if previous_ftp is None:
            try:
                athlete = self.builder.build()
                previous_ftp = getattr(athlete, "ftp", None)
            except Exception:
                previous_ftp = None

        today = dt_util.now().date()
        result = {
            **self._ftp_test_result,
            "status": "provisional",
            "power_20min": round(power, 1),
            "ftp_95": round(ftp_value, 1),
            "previous_ftp": previous_ftp,
            "ftp_recommended": None,
            "confidence": None,
            "coverage_percent": None,
            "power_source": "manual_activity_screen",
            "power_std_percent": None,
            "split_difference_percent": None,
            "activity_id": None,
            "test_date": today.isoformat(),
            "last_test_date": today.isoformat(),
            "next_test_date": None,
            "auto_scheduled": False,
            "manual_result": True,
            "validation_pending": True,
            "validation_status": "pending_athena",
            "athena_validation": {
                "status": "pending_athena",
                "message": "Resultado introducido manualmente; pendiente de validación con la serie y el contexto de Athena.",
            },
            "ftp_auto_accepted": False,
            "message": (
                f"Resultado manual provisional: {power:.1f} W en 20 min -> "
                f"FTP estimado {ftp_value:.1f} W. Pendiente de validar con "
                "la serie de potencia. El FTP de Garmin no se ha modificado."
            ),
            "analyzed_at": dt_util.now().isoformat(),
        }

        self._ftp_test_result = result
        await self._persist_ftp_test_result()
        self.async_update_listeners()

        try:
            await self.notifier.send(
                "Coach AI - FTP provisional",
                (
                    f"20 min: {power:.1f} W\n"
                    f"FTP estimado: {ftp_value:.1f} W\n"
                    f"FTP anterior: {previous_ftp or 'N/D'} W\n"
                    "Estado: PROVISIONAL\n"
                    "Pendiente de validar. El FTP de Garmin no se ha modificado."
                ),
            )
        except Exception:
            _LOGGER.exception("Coach AI FTP: no se pudo notificar el resultado manual.")

        return result

    async def _persist_ftp_test_result(self) -> None:
        """Persiste el estado del ciclo FTP en el historial de Coach AI."""
        try:
            records = await self.history.load()
            records = [r for r in records if r.get("type") != "ftp_test_state"]
            records.append({
                "timestamp": dt_util.now().isoformat(),
                "date": dt_util.now().date().isoformat(),
                "type": "ftp_test_state",
                "status": self._ftp_test_result.get("status"),
                "ftp_test": dict(self._ftp_test_result),
            })
            await self.history.save_records(records)
        except Exception:
            _LOGGER.exception("Coach AI FTP: no se pudo persistir el estado del test.")

    async def _restore_ftp_test_result(self, history_records: list[dict[str, Any]]) -> None:
        """Restaura el último estado FTP tras reiniciar Home Assistant."""
        if self._ftp_test_loaded:
            return
        for record in reversed(history_records):
            if record.get("type") != "ftp_test_state":
                continue
            saved = record.get("ftp_test")
            if isinstance(saved, dict):
                self._ftp_test_result = {**self._ftp_test_result, **saved}
            break
        self._ftp_test_loaded = True

    async def _maybe_schedule_ftp_test(self) -> None:
        """Programa un nuevo test cuando han transcurrido 6 semanas."""
        if self._ftp_test_auto_running:
            return
        next_date_raw = self._ftp_test_result.get("next_test_date")
        if not next_date_raw:
            return
        try:
            next_date = date.fromisoformat(str(next_date_raw)[:10])
        except (TypeError, ValueError):
            return
        today = dt_util.now().date()
        if today < next_date:
            return
        pending_date = self._ftp_test_result.get("test_date")
        if self._ftp_test_result.get("status") in {"scheduled", "generated", "pending_data"} and pending_date:
            try:
                if date.fromisoformat(str(pending_date)[:10]) >= today:
                    return
            except (TypeError, ValueError):
                pass
        self._ftp_test_auto_running = True
        try:
            tomorrow = today + timedelta(days=1)
            await self.async_start_ftp_test(test_date=tomorrow, automatic=True)
            await self.notifier.send(
                "🧪 Coach AI · Nuevo test FTP",
                f"Han pasado 6 semanas desde el último ciclo FTP.\nNuevo test programado para {tomorrow.isoformat()}.",
            )
        except Exception:
            _LOGGER.exception("Coach AI FTP: error programando el test automático de 6 semanas.")
        finally:
            self._ftp_test_auto_running = False

    # ============================================================
    # ANÁLISIS AUTOMÁTICO DEL TEST FTP
    # ============================================================

    @staticmethod
    def _numeric_state_value(value: Any) -> float | None:
        """Convierte un estado HA a número, tolerando unidades y texto."""
        if value is None:
            return None
        try:
            number = float(value)
            return number if number > 0 else None
        except (TypeError, ValueError):
            import re

            match = re.search(r"(-?\d+(?:[.,]\d+)?)", str(value))
            if not match:
                return None
            try:
                number = float(match.group(1).replace(",", "."))
                return number if number > 0 else None
            except ValueError:
                return None

    def _get_intervals_ftp(self) -> tuple[float | None, str | None]:
        """Busca eFTP/FTP de Intervals.icu sin depender de un entity_id fijo."""
        candidates: list[tuple[float, str]] = []

        for state in self.hass.states.async_all("sensor"):
            haystack = f"{state.entity_id} {state.name}".lower()
            if "intervals" not in haystack:
                continue
            if "eftp" not in haystack and "ftp" not in haystack:
                continue

            value = self._numeric_state_value(state.state)
            if value is not None:
                candidates.append((
                    0 if "eftp" in haystack else 1,
                    value,
                    state.entity_id,
                ))

        if not candidates:
            return None, None

        # Preferir eFTP explícito sobre un sensor genérico de FTP.
        candidates.sort(
            key=lambda item: (item[0], item[2]),
        )
        _, value, entity_id = candidates[0]
        return value, entity_id

    @staticmethod
    def _is_ftp_test_activity(activity: Any, pending_test_date: str | None) -> bool:
        """Determina si una actividad corresponde al test FTP."""
        name = str(
            getattr(activity, "activity_name", "") or ""
        ).strip().lower()
        compact = name.replace("_", " ").replace("-", " ")

        strong_name = (
            "ftp test" in compact
            or "test ftp" in compact
            or "prueba ftp" in compact
            or ("ftp" in compact and "20 min" in compact)
        )
        if strong_name:
            return True

        if not pending_test_date:
            return False

        activity_start = getattr(activity, "start_time", None)
        if isinstance(activity_start, str):
            try:
                activity_start = dt_util.parse_datetime(activity_start)
            except (TypeError, ValueError):
                activity_start = None

        if activity_start is None:
            return False

        try:
            activity_date = (
                dt_util.as_local(activity_start)
                .date()
                .isoformat()
            )
        except Exception:
            try:
                activity_date = activity_start.date().isoformat()
            except Exception:
                return False

        duration = getattr(activity, "duration", None)
        try:
            duration_value = float(duration) if duration is not None else 0.0
        except (TypeError, ValueError):
            duration_value = 0.0

        return (
            activity_date == pending_test_date
            and 50 <= duration_value <= 70
            and str(getattr(activity, "activity_type", "") or "").lower()
            in {
                "cycling",
                "bike",
                "indoor_cycling",
                "indoorcycling",
                "indoor cycling",
                "virtualride",
                "cycling_indoor",
                "stationarybike",
                "",
            }
        )

    @staticmethod
    def _validate_ftp_with_athena(
        analysis: Any,
        athena: Any | None,
        previous_ftp: float | int | None,
    ) -> tuple[str, str, bool]:
        """Cruza la calidad del test con el estado actual de Athena.

        No cambia el FTP de Garmin. Solo decide si Coach AI puede considerar
        el resultado validado, si debe dejarlo pendiente o si debe rechazarlo.
        La calidad de la serie sigue siendo responsabilidad de FTPTestEngine;
        Athena aporta el contexto de recuperación/fatiga del día.
        """
        status = str(getattr(analysis, "status", "invalid") or "invalid")
        confidence = float(getattr(analysis, "confidence", 0) or 0)
        coverage = float(getattr(analysis, "coverage_percent", 0) or 0)
        power_source = str(getattr(analysis, "power_source", "") or "")

        if status == "invalid":
            return (
                "rejected",
                "La serie de potencia no supera los criterios de calidad del test.",
                False,
            )

        # Para aceptar automáticamente exigimos datos medidos y completos.
        # Los resultados parciales/estimados nunca pasan directamente a FTP aceptado.
        data_ok = (
            status == "valid"
            and confidence >= 80.0
            and coverage >= 95.0
            and power_source != "estimated"
        )
        if not data_ok:
            return (
                "pending_data_quality",
                "El resultado es útil, pero Athena espera una validación adicional de la calidad de los datos.",
                False,
            )

        if athena is None:
            return (
                "pending_athena",
                "Test técnicamente válido; falta el contexto de Athena para aceptarlo.",
                False,
            )

        recovery = float(getattr(athena, "recovery_score", 0) or 0)
        recommendation = str(getattr(athena, "recommendation", "") or "").strip().lower()
        risk_score = float(getattr(athena, "overtraining_score", 0) or 0)

        # Usamos las propias categorías de Athena: con recuperación >=60
        # Athena considera la situación apta para entrenamiento normal/intenso.
        # Si está en recuperación activa/descanso o riesgo alto, no fijamos un FTP
        # nuevo aunque la serie sea matemáticamente válida.
        context_ok = (
            recovery >= 60.0
            and recommendation in {
                "entrenamiento normal",
                "entrenamiento intenso",
            }
            and risk_score < 70.0
        )

        if not context_ok:
            return (
                "pending_athena",
                (
                    f"Test válido ({confidence:.0f}% de confianza), pero Athena no lo acepta todavía: "
                    f"Recovery {recovery:.0f}%, recomendación '{recommendation or 'N/D'}', "
                    f"riesgo {risk_score:.0f}."
                ),
                False,
            )

        previous = float(previous_ftp or 0)
        new_ftp = float(getattr(analysis, "ftp_95", 0) or 0)
        change = abs(new_ftp - previous) / previous * 100 if previous > 0 else 0.0

        # Una caída/subida muy grande no se acepta de forma silenciosa: se deja
        # validada técnicamente pero pendiente de confirmación.
        if previous > 0 and change > 15.0:
            return (
                "pending_confirmation",
                (
                    f"Test válido y contexto de Athena favorable, pero el FTP cambia un {change:.1f}%. "
                    "Se requiere confirmación antes de usarlo como nuevo FTP."
                ),
                False,
            )

        return (
            "accepted",
            "Test válido, datos completos y contexto de Athena favorable. Resultado aceptado por Coach AI; Garmin no se modifica.",
            True,
        )

    async def _analyse_ftp_test_activity(
        self,
        activity: Any | None,
        athlete: Any | None = None,
        athena: Any | None = None,
    ) -> None:
        """Analiza automáticamente la actividad real del test FTP."""
        if activity is None:
            return

        previous_result = dict(self._ftp_test_result)
        activity_id = getattr(activity, "activity_id", None)

        if (
            activity_id is None
            or previous_result.get("activity_id") == activity_id
            and previous_result.get("status") in {"valid", "partial"}
        ):
            return

        pending_date = previous_result.get("test_date")
        if not self._is_ftp_test_activity(activity, pending_date):
            return

        previous_ftp = previous_result.get("previous_ftp")
        if previous_ftp is None and athlete is not None:
            previous_ftp = getattr(athlete, "ftp", None)

        intervals_ftp, intervals_entity = self._get_intervals_ftp()

        _LOGGER.info(
            "Coach AI FTP: actividad candidata detectada | id=%s | nombre=%s | "
            "fecha=%s | eFTP=%s (%s)",
            activity_id,
            getattr(activity, "activity_name", None),
            getattr(activity, "start_time", None),
            intervals_ftp,
            intervals_entity,
        )

        try:
            samples = await self.hass.async_add_executor_job(
                self.activity_engine.read_power_samples,
                int(activity_id),
            )
        except Exception:
            _LOGGER.exception(
                "Coach AI FTP: error leyendo serie de potencia | activityId=%s",
                activity_id,
            )
            samples = []

        if not samples:
            self._ftp_test_result = {
                **previous_result,
                "status": "pending_data",
                "activity_id": activity_id,
                "message": (
                    "Actividad FTP detectada, pero todavía no hay serie temporal "
                    "de potencia disponible en Garmin/FIT. Se volverá a intentar."
                ),
            }
            self.async_update_listeners()
            return

        analysis = self.ftp_test.analyse_power_series(
            samples,
            previous_ftp=previous_ftp,
            intervals_ftp=intervals_ftp,
            intervals_entity=intervals_entity,
            activity_id=int(activity_id),
        )

        validation_status, validation_message, auto_accepted = (
            self._validate_ftp_with_athena(
                analysis,
                athena,
                previous_ftp,
            )
        )

        result = {
            **previous_result,
            "status": analysis.status,
            "power_20min": analysis.power_20min,
            "ftp_95": analysis.ftp_95,
            "previous_ftp": analysis.ftp_previous,
            "ftp_intervals": analysis.ftp_intervals,
            "ftp_recommended": analysis.ftp_recommended,
            "confidence": analysis.confidence,
            "message": analysis.message,
            "activity_id": analysis.activity_id,
            "window_start_seconds": analysis.window_start_seconds,
            "window_end_seconds": analysis.window_end_seconds,
            "coverage_percent": analysis.coverage_percent,
            "power_source": analysis.power_source,
            "power_std_percent": analysis.power_std_percent,
            "split_difference_percent": analysis.split_difference_percent,
            "intervals_entity": analysis.intervals_entity,
            "validation_status": validation_status,
            "athena_validation": {
                "status": validation_status,
                "message": validation_message,
                "recovery_score": getattr(athena, "recovery_score", None),
                "recommendation": getattr(athena, "recommendation", None),
                "overtraining_score": getattr(athena, "overtraining_score", None),
            },
            "ftp_auto_accepted": auto_accepted,
            "validation_pending": not auto_accepted,
            "analyzed_at": dt_util.now().isoformat(),
            "activity_name": getattr(activity, "activity_name", None),
            "activity_start": (
                getattr(activity, "start_time", None).isoformat()
                if hasattr(getattr(activity, "start_time", None), "isoformat")
                else getattr(activity, "start_time", None)
            ),
        }

        if auto_accepted:
            completed_date = dt_util.now().date()
            result["last_test_date"] = completed_date.isoformat()
            result["next_test_date"] = (completed_date + timedelta(days=42)).isoformat()
            result["auto_scheduled"] = False

        self._ftp_test_result = result
        await self._persist_ftp_test_result()
        self.async_update_listeners()

        if analysis.status in {"valid", "partial", "invalid"}:
            try:
                await self.notifier.send(
                    "🧪 Coach AI · Resultado FTP",
                    (
                        f"Actividad {getattr(activity, 'activity_name', 'FTP Test')} analizada.\n"
                        f"Potencia 20 min: {analysis.power_20min:.1f} W\n"
                        f"FTP estimado: {analysis.ftp_95:.1f} W\n"
                        f"Confianza: {analysis.confidence:.0f}%\n"
                        f"Estado técnico: {analysis.status}\n"
                        f"Validación Athena: {validation_status}\n"
                        f"{validation_message}\n"
                        "El FTP real de Garmin no se ha modificado."
                    ),
                )
            except Exception:
                _LOGGER.exception(
                    "Coach AI FTP: no se pudo enviar la notificación del resultado."
                )

        _LOGGER.info(
            "Coach AI FTP: análisis completado | activityId=%s | status=%s | "
            "20min=%s W | ftp95=%s W | recomendado=%s W | confianza=%s%%",
            activity_id,
            analysis.status,
            analysis.power_20min,
            analysis.ftp_95,
            analysis.ftp_recommended,
            analysis.confidence,
        )

    @staticmethod
    def _training_to_dict(training: Any) -> dict[str, Any] | None:
        """Convierte un TrainingPlan a un diccionario persistible."""
        if training is None:
            return None

        data = {
            "workout": getattr(training, "workout", None),
            "duration": getattr(training, "duration", None),
            "zone": getattr(training, "zone", None),
            "target_power": getattr(training, "target_power", None),
            "target_hr": getattr(training, "target_hr", None),
            "cadence": getattr(training, "cadence", None),
            "target_tss": getattr(training, "target_tss", None),
            "intensity_factor": getattr(training, "intensity_factor", None),
            "outdoor": getattr(training, "outdoor", False),
            "reason": getattr(training, "reason", None),
            # Desde la corrección de TrainingEngine, Interval.duration se
            # almacena en segundos. Guardamos la unidad explícitamente para
            # evitar ambigüedades al persistir y reconstruir el plan.
            "interval_duration_unit": "seconds",
            "intervals": [],
        }

        intervals = getattr(training, "intervals", None)
        if intervals:
            for interval in intervals:
                if isinstance(interval, dict):
                    data["intervals"].append(interval)
                else:
                    data["intervals"].append(
                        {
                            "name": getattr(interval, "name", None),
                            "duration": getattr(interval, "duration", None),
                            "zone": getattr(interval, "zone", None),
                            "target_power": getattr(
                                interval,
                                "power",
                                getattr(interval, "target_power", None),
                            ),
                            "target_hr": getattr(
                                interval,
                                "heart_rate",
                                getattr(interval, "target_hr", None),
                            ),
                            "cadence": getattr(interval, "cadence", None),
                            "step_type": getattr(interval, "step_type", "interval"),
                            "intensity": getattr(interval, "intensity", "active"),
                        }
                    )

        export = getattr(training, "export", None)
        if isinstance(export, dict):
            data["export"] = export

        return data

    @staticmethod
    def _training_from_dict(data: dict[str, Any] | None) -> TrainingPlan | None:
        """Reconstruye un TrainingPlan desde el historial.

        Los planes nuevos guardan Interval.duration en segundos. Los planes
        antiguos no tenían unidad y almacenaban minutos; se detectan por su
        magnitud típica y se convierten una sola vez durante la carga.
        """
        if not isinstance(data, dict):
            return None

        intervals: list[Interval] = []
        serialized = data.get("intervals", [])

        raw_durations: list[int] = []
        if isinstance(serialized, list):
            for item in serialized:
                if isinstance(item, dict):
                    try:
                        value = int(item.get("duration") or 0)
                    except (TypeError, ValueError):
                        value = 0
                    if value > 0:
                        raw_durations.append(value)

        duration_unit = str(
            data.get("interval_duration_unit") or ""
        ).strip().lower()

        if duration_unit == "seconds":
            legacy_minutes = False
        elif duration_unit == "minutes":
            legacy_minutes = True
        else:
            # Compatibilidad con registros históricos creados antes de la
            # corrección: los workouts actuales tienen pasos de cientos o
            # miles de segundos; los antiguos usaban valores como 10, 15,
            # 40 o 45 (minutos).
            legacy_minutes = bool(
                raw_durations
                and max(raw_durations) <= 180
            )

        if isinstance(serialized, list):
            for item in serialized:
                if not isinstance(item, dict):
                    continue

                try:
                    duration = int(item.get("duration") or 0)
                except (TypeError, ValueError) as err:
                    raise ValueError(
                        f"Duración de intervalo no válida: {item.get('duration')!r}"
                    ) from err

                if legacy_minutes and duration > 0:
                    duration *= 60

                intervals.append(
                    Interval(
                        name=item.get("name") or "Intervalo",
                        duration=duration,
                        power=item.get("target_power"),
                        heart_rate=item.get("target_hr"),
                        cadence=item.get("cadence"),
                        step_type=item.get("step_type", "interval"),
                        intensity=item.get("intensity", "active"),
                    )
                )

        return TrainingPlan(
            workout=data.get("workout") or "Unknown",
            duration=int(data.get("duration") or 0),
            zone=data.get("zone"),
            target_power=data.get("target_power"),
            target_hr=data.get("target_hr"),
            cadence=data.get("cadence"),
            target_tss=data.get("target_tss"),
            intensity_factor=data.get("intensity_factor"),
            outdoor=data.get("outdoor", False),
            reason=data.get("reason") or "",
            intervals=intervals,
            export=data.get("export", {}),
        )

    @staticmethod
    def _effective_day_preference(
        day_index: int,
        unavailable_days: set[int],
        requested_rest_days: set[int],
        requested_training_days: set[int],
    ) -> str:
        """Obtiene la preferencia efectiva que provocó el plan."""
        if day_index in unavailable_days:
            return "No disponible"
        if day_index in requested_rest_days:
            return "Descanso"
        if day_index in requested_training_days:
            return "Entrenamiento"
        return "Athena"

    @staticmethod
    def _garmin_workout_signature(
        workout_data: dict[str, Any],
        workout_date: date,
    ) -> str:
        """Genera una firma estable para evitar subir dos veces el mismo workout."""
        payload = {
            "date": workout_date.isoformat(),
            "workout": workout_data,
        }
        encoded = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            default=str,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()[:24]

    async def _sync_training_to_garmin(
        self,
        training: TrainingPlan,
        workout_date: date,
        existing_garmin: dict[str, Any] | None = None,
        *,
        force_replacement: bool = False,
    ) -> tuple[bool, Any | None, Any | None]:
        """Sube y programa un entrenamiento en Garmin Connect."""
        if not training or not training.intervals:
            _LOGGER.debug(
                "Coach AI Garmin MCP: %s sin intervalos; no se envía.",
                getattr(training, "workout", None),
            )
            return False, None, None

        now = dt_util.now()
        if (
            self._garmin_sync_blocked_until is not None
            and now < self._garmin_sync_blocked_until
        ):
            _LOGGER.debug(
                "Coach AI Garmin MCP: sincronización temporalmente pausada hasta %s; "
                "Athena continúa funcionando normalmente.",
                self._garmin_sync_blocked_until.isoformat(),
            )
            return False, None, None

        garmin = self.workout_exporter.garmin_builder.build(training)
        steps: list[dict[str, Any]] = []

        for step in garmin.steps:
            duration = int(getattr(step, "duration", 0) or 0)
            if duration <= 0:
                raise GarminMCPError(
                    f"Duración inválida en paso Garmin: {getattr(step, 'name', 'Intervalo')!r} "
                    f"({duration} s)."
                )

            target_type = getattr(step, "target_type", None)
            _LOGGER.info(
                "Coach AI Garmin STEP | name=%s | duration=%ss (%.1fmin) | "
                "target=%s | type=%s | intensity=%s | power=%s-%s | cadence=%s-%s",
                getattr(step, "name", "Intervalo"),
                duration,
                duration / 60.0,
                target_type,
                getattr(step, "step_type", "interval"),
                getattr(step, "intensity", "active"),
                getattr(step, "power_low", None),
                getattr(step, "power_high", None),
                getattr(step, "cadence_low", None),
                getattr(step, "cadence_high", None),
            )

            step_type = str(
                getattr(step, "step_type", "interval") or "interval"
            ).strip().lower()

            intensity = str(
                getattr(step, "intensity", "active") or "active"
            ).strip().lower()

            # Normalizamos los tipos admitidos para evitar enviar valores
            # desconocidos al constructor Garmin.
            if step_type not in {
                "warmup",
                "interval",
                "recovery",
                "cooldown",
            }:
                step_type = "interval"

            if intensity not in {
                "warmup",
                "active",
                "rest",
                "cooldown",
            }:
                intensity = (
                    "warmup"
                    if step_type == "warmup"
                    else "cooldown"
                    if step_type == "cooldown"
                    else "rest"
                    if step_type == "recovery"
                    else "active"
                )

            _LOGGER.info(
                "Coach AI Garmin STEP TYPE | name=%s | step_type=%s | intensity=%s",
                getattr(step, "name", "Intervalo"),
                step_type,
                intensity,
            )

            steps.append(
                {
                    "name": getattr(step, "name", "Intervalo"),
                    "duration": getattr(step, "duration", 0),
                    "target_type": target_type,
                    "target_low": (
                        getattr(step, "power_low", None)
                        if target_type == "power"
                        else getattr(step, "hr_low", None)
                        if target_type == "heart_rate"
                        else getattr(step, "cadence_low", None)
                        if target_type == "cadence"
                        else None
                    ),
                    "target_high": (
                        getattr(step, "power_high", None)
                        if target_type == "power"
                        else getattr(step, "hr_high", None)
                        if target_type == "heart_rate"
                        else getattr(step, "cadence_high", None)
                        if target_type == "cadence"
                        else None
                    ),
                    "step_type": step_type,
                    "intensity": intensity,
                }
            )

        workout_name = str(training.workout or "Coach AI")
        workout_data = build_garmin_cycling_workout(
            name=workout_name,
            description=str(training.reason or "Coach AI")[:1000],
            steps=steps,
        )

        signature = self._garmin_workout_signature(workout_data, workout_date)
        current = existing_garmin if isinstance(existing_garmin, dict) else {}
        stored_signature = str(
            current.get("workout_signature")
            or current.get("previous_workout_signature")
            or ""
        )
        stored_workout_id = current.get("workout_id") or current.get("previous_workout_id")
        stored_scheduled = bool(
            current.get("scheduled")
            or current.get("previous_scheduled")
        )
        replacement_pending = bool(current.get("replacement_pending"))

        # Protección persistente: si este mismo workout ya está programado,
        # no se vuelve a subir aunque Home Assistant se haya reiniciado.
        if stored_scheduled and stored_workout_id and not stored_signature and not replacement_pending:
            # Migración segura de planes creados por versiones anteriores que
            # ya estaban programados pero no guardaban firma. Asociamos el ID
            # existente al plan actual sin volver a subirlo.
            await self.history.update_frozen_garmin(
                workout_date.isoformat(),
                workout_id=int(stored_workout_id),
                workout_signature=signature,
                scheduled=True,
                uploaded=True,
            )
            _LOGGER.info(
                "Coach AI Garmin: plan antiguo migrado sin duplicar | date=%s | id=%s",
                workout_date,
                stored_workout_id,
            )
            return (
                True,
                {"workout_id": int(stored_workout_id), "cached": True},
                current.get("scheduled_result"),
            )

        if stored_scheduled and not stored_workout_id:
            if force_replacement:
                try:
                    async with GarminMCPClient() as client:
                        tools = await client.list_tools()
                        tool_names = [
                            str(tool.get("name"))
                            for tool in tools
                            if isinstance(tool, dict) and tool.get("name")
                        ]
                        _LOGGER.warning(
                            "Coach AI Garmin TOOLS | disponibles=%s",
                            tool_names,
                        )
                        candidates = [
                            tool
                            for tool in tools
                            if isinstance(tool, dict)
                            and any(
                                token in str(tool.get("name", "")).lower()
                                for token in ("delete", "remove", "unschedule", "cancel")
                            )
                        ]
                        if candidates:
                            _LOGGER.warning(
                                "Coach AI Garmin TOOLS | candidatos eliminación=%s",
                                candidates,
                            )
                        else:
                            _LOGGER.warning(
                                "Coach AI Garmin TOOLS | no aparece herramienta de eliminación/desprogramación.",
                            )
                except Exception as err:
                    _LOGGER.warning(
                        "Coach AI Garmin: no se pudieron consultar tools/list: %s",
                        err,
                    )
            _LOGGER.warning(
                "Coach AI Garmin: el historial indica scheduled=True pero no tiene workout_id; "
                "se bloquea una nueva subida para evitar duplicados | date=%s",
                workout_date,
            )
            return False, None, None

        if stored_signature == signature and stored_scheduled and stored_workout_id:
            _LOGGER.info(
                "Coach AI Garmin: workout ya programado; no se duplica | date=%s | id=%s",
                workout_date,
                stored_workout_id,
            )
            return (
                True,
                {"workout_id": int(stored_workout_id), "cached": True},
                current.get("scheduled_result"),
            )

        # Sustitución segura: solo tras una acción explícita (recalcular o cambiar
        # la preferencia del día). Se desprograma el evento de calendario, nunca
        # se borra automáticamente la plantilla de Garmin.
        if stored_scheduled and stored_workout_id and stored_signature != signature:
            if not (force_replacement or replacement_pending):
                _LOGGER.warning(
                    "Coach AI Garmin: ya existe otro workout programado para %s (id=%s); "
                    "no se sustituye sin recálculo explícito.",
                    workout_date, stored_workout_id,
                )
                return False, None, None

            try:
                async with GarminMCPClient() as client:
                    entries = extract_records(await client.get_scheduled_workouts(
                        workout_date.isoformat(), workout_date.isoformat()
                    ))
                    old_id = int(stored_workout_id)
                    matching = []
                    for entry in entries:
                        event_workout_id = entry.get("workout_id", entry.get("workoutId"))
                        event_date = entry.get("calendar_date", entry.get("date", entry.get("scheduled_date")))
                        if str(event_workout_id) == str(old_id) and (not event_date or str(event_date)[:10] == workout_date.isoformat()):
                            event_id = entry.get("scheduled_workout_id", entry.get("scheduledWorkoutId"))
                            if event_id is not None:
                                matching.append((int(event_id), entry))

                    if len(matching) != 1:
                        _LOGGER.error(
                            "Coach AI Garmin: sustitución bloqueada por seguridad; se esperaba "
                            "un evento de calendario para workout_id=%s en %s y se encontraron %s. "
                            "No se ha desprogramado ni subido nada.",
                            old_id, workout_date, len(matching),
                        )
                        return False, None, None

                    scheduled_event_id, old_entry = matching[0]
                    await client.unschedule_workout(scheduled_event_id)
                    _LOGGER.warning(
                        "Coach AI Garmin: evento anterior desprogramado para sustituirlo | "
                        "fecha=%s | scheduled_workout_id=%s | workout_id=%s",
                        workout_date, scheduled_event_id, old_id,
                    )
                    # Limpiamos el estado activo antes de subir el nuevo. Se conserva
                    # el ID antiguo solo como dato histórico y no se elimina su plantilla.
                    if existing_garmin is not None:
                        await self.history.update_frozen_garmin(
                            workout_date.isoformat(),
                            workout_id=None,
                            workout_signature=None,
                            scheduled=False,
                            uploaded=False,
                            scheduled_workout_id=None,
                            replacement_pending=True,
                            previous_workout_id=old_id,
                            previous_scheduled=False,
                            previous_scheduled_workout_id=scheduled_event_id,
                        )
            except GarminMCPError as err:
                _LOGGER.error(
                    "Coach AI Garmin: no se pudo desprogramar de forma segura el workout anterior; "
                    "se cancela la sustitución sin subir otro. Detalle: %s", err,
                )
                return False, None, None
            except Exception as err:
                _LOGGER.exception(
                    "Coach AI Garmin: fallo inesperado preparando la sustitución; "
                    "no se subirá otro workout. Detalle: %s", err,
                )
                return False, None, None

        try:
            async with GarminMCPClient() as client:
                # Subimos primero, pero persistimos el workout_id antes de
                # programarlo. Si schedule falla, el siguiente intento reutiliza
                # este ID y no crea un segundo workout en Garmin.
                if stored_workout_id and stored_signature == signature and not stored_scheduled:
                    workout_id = int(stored_workout_id)
                    uploaded = {
                        "workout_id": workout_id,
                        "cached": True,
                    }
                    _LOGGER.info(
                        "Coach AI Garmin: reutilizando workout pendiente | id=%s | date=%s",
                        workout_id,
                        workout_date,
                    )
                else:
                    uploaded, workout_id = await client.upload_workout_with_id(
                        workout_data
                    )

                # Persistimos el ID ANTES de programar. Si Garmin falla después de
                # crear el workout, el siguiente intento reutiliza este mismo ID.
                if existing_garmin is not None:
                    await self.history.update_frozen_garmin(
                        workout_date.isoformat(),
                        workout_id=int(workout_id),
                        workout_signature=signature,
                        uploaded=True,
                        scheduled=False,
                        scheduled_date=workout_date.isoformat(),
                        uploaded_result=str(uploaded)[:2000],
                    )

                scheduled = await client.schedule_workout(
                    workout_id,
                    workout_date.isoformat(),
                )
        except GarminMCPError as err:
            # Garmin es un servicio externo: una caída del Bridge no debe
            # convertir el coordinator en unavailable ni impedir recalcular Athena.
            self._garmin_sync_blocked_until = dt_util.now() + timedelta(minutes=10)
            _LOGGER.warning(
                "Coach AI Garmin MCP: no se pudo subir/programar %s para %s. "
                "Athena continúa; se reintentará tras el enfriamiento de 10 min. "
                "Detalle: %s",
                workout_name,
                workout_date,
                err,
            )
            return False, None, None
        except Exception as err:
            self._garmin_sync_blocked_until = dt_util.now() + timedelta(minutes=5)
            _LOGGER.exception(
                "Coach AI Garmin MCP: error inesperado sincronizando %s para %s.",
                workout_name,
                workout_date,
            )
            return False, None, None

        _LOGGER.info(
            "Coach AI Garmin MCP: entrenamiento enviado y programado | workout=%s | fecha=%s",
            workout_name,
            workout_date,
        )
        return True, uploaded, scheduled

    async def _prepare_daily_plan(
        self,
        athena: Any,
        unavailable_days: set[int],
        requested_rest_days: set[int],
        requested_training_days: set[int],
    ) -> tuple[TrainingPlan | None, dict[str, Any] | None, bool]:
        """Obtiene/congela el entrenamiento de hoy y devuelve si cambió."""
        today = dt_util.now().date()
        day_index = today.weekday()
        preference = self._effective_day_preference(
            day_index,
            unavailable_days,
            requested_rest_days,
            requested_training_days,
        )

        weekly_plan = getattr(athena, "week", None) or []
        today_training = (
            weekly_plan[day_index]
            if day_index < len(weekly_plan)
            else getattr(athena, "training", None)
        )

        # Una preferencia explícita de descanso/no disponibilidad tiene prioridad
        # sobre la propuesta de Athena (que puede ser None o seguir siendo Recovery).
        # Se persiste como plan real para que el día congelado también se actualice.
        if preference in {"No disponible", "Descanso"}:
            non_workout_name = preference
            today_training = TrainingPlan(
                workout=non_workout_name,
                duration=0,
                zone=None,
                target_power=None,
                target_hr=None,
                cadence=None,
                target_tss=0,
                intensity_factor=0,
                outdoor=False,
                reason=(
                    "Día marcado como no disponible por el atleta."
                    if preference == "No disponible"
                    else "Día marcado como descanso por el atleta."
                ),
                intervals=[],
                export={},
            )

        existing = await self.history.frozen_plan_record_for_date(
            today.isoformat()
        )
        previous_garmin = (
            dict(existing.get("garmin"))
            if isinstance(existing, dict)
            and isinstance(existing.get("garmin"), dict)
            else {}
        )

        # Detectar planes congelados antiguos que todavía guardan sus
        # intervalos en minutos. Al regenerarlos una vez quedan persistidos
        # en segundos y se fuerza una nueva sincronización con Garmin.
        legacy_duration_record = False
        if isinstance(existing, dict):
            existing_training = existing.get("training")
            if isinstance(existing_training, dict):
                existing_unit = str(
                    existing_training.get("interval_duration_unit") or ""
                ).strip().lower()
                serialized_intervals = existing_training.get("intervals", [])
                legacy_values: list[int] = []
                if isinstance(serialized_intervals, list):
                    for item in serialized_intervals:
                        if not isinstance(item, dict):
                            continue
                        try:
                            value = int(item.get("duration") or 0)
                        except (TypeError, ValueError):
                            value = 0
                        if value > 0:
                            legacy_values.append(value)

                legacy_duration_record = (
                    existing_unit != "seconds"
                    and bool(legacy_values)
                    and max(legacy_values) <= 180
                )

        needs_new = existing is None
        if existing is not None and self._force_recalculate:
            needs_new = True
        elif existing is not None:
            previous_preference = str(existing.get("preference") or "Athena")
            if previous_preference != preference:
                needs_new = True
            elif preference in {"No disponible", "Descanso"}:
                old_training = existing.get("training")
                old_workout = str(old_training.get("workout", "") if isinstance(old_training, dict) else "").strip().lower()
                expected = "no disponible" if preference == "No disponible" else "descanso"
                if old_workout != expected:
                    needs_new = True
            elif legacy_duration_record and today_training is not None:
                needs_new = True

        changed = False
        if needs_new and today_training is not None:
            source = (
                "manual"
                if self._force_recalculate
                else "preference_change"
                if existing is not None and not legacy_duration_record
                else "duration_unit_migration"
                if legacy_duration_record
                else "daily"
            )
            changed = await self.history.save_frozen_training(
                today.isoformat(),
                today_training,
                source=source,
                preference=preference,
                replace=True,
            )
            existing = await self.history.frozen_plan_record_for_date(
                today.isoformat()
            )

            # Si sustituimos un plan que ya estaba programado en Garmin,
            # conservamos su referencia para desprogramar solo el evento antiguo.
            if previous_garmin.get("scheduled") or previous_garmin.get("workout_id"):
                await self.history.update_frozen_garmin(
                    today.isoformat(),
                    previous_workout_id=previous_garmin.get("workout_id"),
                    previous_workout_signature=previous_garmin.get("workout_signature"),
                    previous_scheduled=previous_garmin.get("scheduled"),
                    previous_scheduled_date=previous_garmin.get("scheduled_date"),
                    previous_uploaded_result=previous_garmin.get("uploaded_result"),
                    previous_scheduled_workout_id=previous_garmin.get("scheduled_workout_id"),
                    replacement_pending=True,
                )
                existing = await self.history.frozen_plan_record_for_date(
                    today.isoformat()
                )

        self._force_recalculate = False

        frozen_data = None
        if isinstance(existing, dict):
            candidate = existing.get("training")
            if isinstance(candidate, dict):
                frozen_data = candidate

        frozen_training = self._training_from_dict(frozen_data)
        return frozen_training, existing, changed

    # ============================================================
    # TSS POR PERIODO
    # ============================================================

    @staticmethod
    def _calculate_period_tss(
        history_records: list[dict[str, Any]],
        days: int,
    ) -> float:
        """Calcula TSS de un periodo evitando duplicados diarios."""

        if not history_records:
            return 0.0

        now = dt_util.now()

        start = now - timedelta(
            days=days - 1
        )

        daily_tss: dict[Any, float] = {}

        for record in history_records:

            timestamp = record.get(
                "timestamp"
            )

            if not timestamp:
                continue

            try:
                record_date = (
                    dt_util.parse_datetime(
                        str(timestamp)
                    )
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            if record_date is None:
                continue

            # ----------------------------------------------------
            # NORMALIZAR TIMEZONE
            # ----------------------------------------------------

            if record_date.tzinfo is None:
                record_date = record_date.replace(
                    tzinfo=now.tzinfo
                )
            else:
                record_date = dt_util.as_local(
                    record_date
                )

            # ----------------------------------------------------
            # FILTRO TEMPORAL
            # ----------------------------------------------------

            if record_date < start:
                continue

            # ----------------------------------------------------
            # ENTRENAMIENTO PLANIFICADO
            # ----------------------------------------------------

            training = record.get(
                "training"
            )

            if not isinstance(
                training,
                dict,
            ):
                continue

            target_tss = training.get(
                "target_tss"
            )

            if target_tss is None:
                continue

            try:
                tss = float(
                    target_tss
                )
            except (
                TypeError,
                ValueError,
            ):
                continue

            # ----------------------------------------------------
            # AGRUPAR POR DÍA
            # ----------------------------------------------------

            day = record_date.date()

            previous = daily_tss.get(
                day
            )

            if (
                previous is None
                or tss > previous
            ):
                daily_tss[day] = tss

        return round(
            sum(daily_tss.values()),
            1,
        )

    # ============================================================
    # FECHA DE ACTIVIDAD GARMIN
    # ============================================================

    @staticmethod
    def _activity_date(
        start_time: str | datetime | date | None,
    ):
        """Obtiene la fecha local de una actividad Garmin.

        Garmin puede entregar start_time como:
        - datetime
        - date
        - str ISO 8601
        """

        if not start_time:
            return None

        try:

            # ----------------------------------------------------
            # YA ES DATETIME
            # ----------------------------------------------------

            if isinstance(
                start_time,
                datetime,
            ):
                parsed = start_time

            # ----------------------------------------------------
            # YA ES DATE
            # ----------------------------------------------------

            elif isinstance(
                start_time,
                date,
            ):
                return start_time

            # ----------------------------------------------------
            # ES STRING
            # ----------------------------------------------------

            else:
                parsed = dt_util.parse_datetime(
                    str(start_time)
                )

            if parsed is None:
                return None

            # ----------------------------------------------------
            # NORMALIZAR TIMEZONE
            # ----------------------------------------------------

            if isinstance(
                parsed,
                datetime,
            ):

                if parsed.tzinfo is None:
                    parsed = parsed.replace(
                        tzinfo=dt_util.now().tzinfo
                    )

                else:
                    parsed = dt_util.as_local(
                        parsed
                    )

                return parsed.date()

            return parsed

        except (
            TypeError,
            ValueError,
            AttributeError,
        ):

            return None

    # ============================================================
    # DETECTAR DESCANSO
    # ============================================================

    @staticmethod
    def _is_rest_training(
        training: dict[str, Any] | None,
    ) -> bool:
        """Determina si un entrenamiento es realmente descanso."""

        if not training:
            return False

        workout = str(
            training.get(
                "workout",
                "",
            )
        ).strip().lower()

        return workout in {
            "rest",
            "descanso",
        }

    # ============================================================
    # GUARDAR ACTIVIDAD EXTRA
    # ============================================================

    async def _save_extra_activity(
        self,
        activity: Any,
        activity_date: Any,
        planned_training: dict[str, Any] | None,
    ) -> bool:
        """Guarda una actividad Garmin realizada fuera del plan."""

        activity_id = getattr(
            activity,
            "activity_id",
            None,
        )

        if activity_id is None:

            _LOGGER.warning(
                "Coach AI DEBUG EXTRA: "
                "actividad sin activity_id."
            )

            return False

        # --------------------------------------------------------
        # DEBUG
        # --------------------------------------------------------

        _LOGGER.warning(
            "Coach AI DEBUG EXTRA: "
            "iniciando guardado | id=%s | fecha=%s | "
            "nombre=%s | tipo=%s | duración=%s | TSS=%s",
            activity_id,
            activity_date,
            getattr(
                activity,
                "activity_name",
                None,
            ),
            getattr(
                activity,
                "activity_type",
                None,
            ),
            getattr(
                activity,
                "duration",
                None,
            ),
            getattr(
                activity,
                "training_load",
                None,
            ),
        )

        # --------------------------------------------------------
        # CARGAR HISTORIAL
        # --------------------------------------------------------

        try:

            records = await self.history.load()

        except Exception:

            _LOGGER.exception(
                "No se pudo cargar el historial para "
                "guardar la actividad extra %s.",
                activity_id,
            )

            return False

        # --------------------------------------------------------
        # EVITAR DUPLICADOS
        # --------------------------------------------------------

        activity_id_str = str(
            activity_id
        )

        for record in records:

            execution = record.get(
                "execution"
            )

            if not isinstance(
                execution,
                dict,
            ):
                continue

            stored_id = execution.get(
                "activity_id"
            )

            if stored_id is None:
                continue

            if str(
                stored_id
            ) == activity_id_str:

                _LOGGER.warning(
                    "Coach AI DEBUG EXTRA: "
                    "actividad %s YA EXISTE en historial.",
                    activity_id,
                )

                return False

        # --------------------------------------------------------
        # ENTRENAMIENTO BASE
        # --------------------------------------------------------

        if isinstance(
            planned_training,
            dict,
        ):

            training = dict(
                planned_training
            )

            _LOGGER.warning(
                "Coach AI DEBUG EXTRA: "
                "entrenamiento base encontrado: %s",
                training,
            )

        else:

            training = {
                "workout": "Extra",
                "duration": 0,
                "zone": None,
                "target_power": None,
                "target_hr": None,
                "cadence": None,
                "target_tss": 0,
                "intensity_factor": None,
                "outdoor": False,
                "reason": (
                    "Actividad realizada fuera "
                    "del entrenamiento planificado."
                ),
                "intervals": [],
            }

            _LOGGER.warning(
                "Coach AI DEBUG EXTRA: "
                "NO había entrenamiento planificado."
            )

        # --------------------------------------------------------
        # REGISTRO DE EJECUCIÓN
        # --------------------------------------------------------

        execution = {
            "activity_id": (
                getattr(
                    activity,
                    "activity_id",
                    None,
                )
            ),
            "activity_name": (
                getattr(
                    activity,
                    "activity_name",
                    None,
                )
            ),
            "activity_type": (
                getattr(
                    activity,
                    "activity_type",
                    None,
                )
            ),
            "start_time": (
                getattr(
                    activity,
                    "start_time",
                    None,
                )
            ),
            "score": 0,
            "duration_real": (
                getattr(
                    activity,
                    "duration",
                    None,
                )
            ),
            "tss_real": (
                getattr(
                    activity,
                    "training_load",
                    None,
                )
            ),
            "power_real": (
                getattr(
                    activity,
                    "avg_power",
                    None,
                )
            ),
            "heart_rate_real": (
                getattr(
                    activity,
                    "avg_hr",
                    None,
                )
            ),
            "cadence_real": None,
            "completion_percent": 0,
            "feedback": (
                "Actividad realizada fuera "
                "del entrenamiento planificado."
            ),
            "status": "EXTRA",
        }

        # --------------------------------------------------------
        # DEBUG
        # --------------------------------------------------------

        _LOGGER.warning(
            "Coach AI DEBUG EXTRA: "
            "execution preparado: %s",
            execution,
        )

        # --------------------------------------------------------
        # REGISTRO COMPLETO
        # --------------------------------------------------------

        record = {
            "timestamp": (
                dt_util.now().isoformat()
            ),
            "date": (
                activity_date.isoformat()
            ),
            "type": "athena_analysis",
            "status": "extra",
            "execution": execution,
            "training": training,
        }

        records.append(
            record
        )

        # --------------------------------------------------------
        # LIMITE DE HISTORIAL
        # --------------------------------------------------------

        if len(records) > self.history.MAX_RECORDS:

            records = records[
                -self.history.MAX_RECORDS:
            ]

        # --------------------------------------------------------
        # DEBUG ANTES DE GUARDAR
        # --------------------------------------------------------

        _LOGGER.warning(
            "Coach AI DEBUG EXTRA: "
            "GUARDANDO actividad %s | fecha=%s | "
            "training=%s | execution=%s",
            activity_id,
            activity_date.isoformat(),
            training,
            execution,
        )

        # --------------------------------------------------------
        # GUARDAR
        # --------------------------------------------------------

        try:

            await self.history.save_records(
                records
            )

        except Exception:

            _LOGGER.exception(
                "Error guardando actividad EXTRA %s.",
                activity_id,
            )

            return False

        _LOGGER.warning(
            "Coach AI DEBUG EXTRA: "
            "GUARDADO CORRECTAMENTE actividad %s "
            "| fecha=%s | TSS=%s | duración=%s",
            activity_id,
            activity_date.isoformat(),
            getattr(
                activity,
                "training_load",
                None,
            ),
            getattr(
                activity,
                "duration",
                None,
            ),
        )

        _LOGGER.info(
            "Coach AI - actividad Garmin %s "
            "guardada como EXTRA | fecha=%s | "
            "TSS=%s | duración=%s min",
            activity_id,
            activity_date.isoformat(),
            getattr(
                activity,
                "training_load",
                None,
            ),
            getattr(
                activity,
                "duration",
                None,
            ),
        )

        return True

    # ============================================================
    # EVALUACIÓN DE ACTIVIDAD REAL
    # ============================================================

    async def _evaluate_last_activity(
        self,
        activity: Any,
        weekly_plan: list[Any] | None = None,
    ) -> Any | None:
        """Evalúa la actividad Garmin contra el plan que quedó congelado.

        El plan diario persistido es la fuente de verdad para el día de
        la actividad. Los planes semanales de Athena se usan únicamente
        como respaldo para datos históricos anteriores al congelado.
        """

        if activity is None:

            _LOGGER.debug(
                "Coach AI DEBUG Garmin: "
                "ActivityEngine devolvió None."
            )

            return None

        # --------------------------------------------------------
        # DEBUG ACTIVIDAD RECIBIDA
        # --------------------------------------------------------

        _LOGGER.debug(
            "Coach AI DEBUG Garmin: "
            "actividad recibida | id=%s | nombre=%s | "
            "tipo=%s | start_time=%s | duración=%s | "
            "TSS=%s | potencia=%s | FC=%s",
            getattr(
                activity,
                "activity_id",
                None,
            ),
            getattr(
                activity,
                "activity_name",
                None,
            ),
            getattr(
                activity,
                "activity_type",
                None,
            ),
            getattr(
                activity,
                "start_time",
                None,
            ),
            getattr(
                activity,
                "duration",
                None,
            ),
            getattr(
                activity,
                "training_load",
                None,
            ),
            getattr(
                activity,
                "avg_power",
                None,
            ),
            getattr(
                activity,
                "avg_hr",
                None,
            ),
        )

        # --------------------------------------------------------
        # ACTIVIDAD INCOMPLETA
        # --------------------------------------------------------
        # Garmin puede publicar primero el activityId y algunos datos
        # básicos, y completar duración/distancia/TSS unos instantes
        # después. No debemos evaluar ni guardar como realizada una
        # actividad que todavía tenga todos esos campos vacíos.
        duration_real = getattr(
            activity,
            "duration",
            None,
        )
        distance_real = getattr(
            activity,
            "distance_km",
            None,
        )
        tss_real = getattr(
            activity,
            "training_load",
            None,
        )

        try:
            duration_value = (
                float(duration_real)
                if duration_real is not None
                else 0.0
            )
        except (
            TypeError,
            ValueError,
        ):
            duration_value = 0.0

        try:
            distance_value = (
                float(distance_real)
                if distance_real is not None
                else 0.0
            )
        except (
            TypeError,
            ValueError,
        ):
            distance_value = 0.0

        if (
            duration_value <= 0
            and distance_value <= 0
            and tss_real is None
        ):
            _LOGGER.debug(
                "Coach AI DEBUG Garmin: "
                "ACTIVIDAD INCOMPLETA | id=%s | "
                "duración=%s | distancia=%s km | TSS=%s. "
                "No se evaluará todavía; Garmin debe completar "
                "los datos y se reintentará en la próxima actualización.",
                getattr(
                    activity,
                    "activity_id",
                    None,
                ),
                duration_real,
                distance_real,
                tss_real,
            )
            return None

        # --------------------------------------------------------
        # ID DE ACTIVIDAD
        # --------------------------------------------------------

        activity_id = getattr(
            activity,
            "activity_id",
            None,
        )

        if activity_id is None:

            _LOGGER.debug(
                "Coach AI DEBUG Garmin: "
                "actividad sin activity_id."
            )

            return None

        # --------------------------------------------------------
        # EVITAR DUPLICADOS
        # --------------------------------------------------------

        try:

            already_exists = (
                await self.history.activity_exists(
                    activity_id
                )
            )

            _LOGGER.debug(
                "Coach AI DEBUG Garmin: "
                "activity_exists(%s) = %s",
                activity_id,
                already_exists,
            )

            if already_exists:

                # La actividad puede haber sido procesada antes de que
                # Garmin expusiera la potencia estimada en el FIT.
                # Si ActivityEngine ya recupera ahora ese dato, rellenamos
                # únicamente power_real sin duplicar ni reevaluar la sesión.
                current_power = getattr(
                    activity,
                    "avg_power",
                    None,
                )

                if current_power is not None:
                    try:
                        repaired = await self.history.update_activity_power(
                            activity_id,
                            current_power,
                        )
                    except Exception:
                        _LOGGER.exception(
                            "Error actualizando la potencia de la actividad "
                            "Garmin %s ya existente.",
                            activity_id,
                        )
                    else:
                        if repaired:
                            _LOGGER.info(
                                "Coach AI - actividad Garmin %s ya existía; "
                                "potencia actualizada a %s W.",
                                activity_id,
                                current_power,
                            )
                        else:
                            _LOGGER.debug(
                                "Coach AI - actividad Garmin %s ya existía "
                                "y no necesitó actualización de potencia.",
                                activity_id,
                            )
                else:
                    _LOGGER.debug(
                        "Actividad Garmin %s ya evaluada y sin potencia nueva.",
                        activity_id,
                    )

                return None

        except Exception:

            _LOGGER.exception(
                "Error comprobando si la actividad "
                "Garmin %s ya existe.",
                activity_id,
            )

            return None

        # --------------------------------------------------------
        # FECHA
        # --------------------------------------------------------

        start_time = getattr(
            activity,
            "start_time",
            None,
        )

        activity_date = self._activity_date(
            start_time
        )

        _LOGGER.debug(
            "Coach AI DEBUG Garmin: "
            "start_time=%s -> activity_date=%s",
            start_time,
            activity_date,
        )

        if activity_date is None:

            _LOGGER.warning(
                "No se pudo determinar la fecha "
                "de la actividad Garmin %s.",
                activity_id,
            )

            return None

        activity_date_str = (
            activity_date.isoformat()
        )

        _LOGGER.debug(
            "Coach AI DEBUG Garmin: "
            "buscando entrenamiento para fecha=%s | "
            "actividad=%s",
            activity_date_str,
            activity_id,
        )

        # --------------------------------------------------------
        # ENTRENAMIENTO PLANIFICADO
        # --------------------------------------------------------
        # La primera referencia es siempre el plan diario congelado.
        # Esto evita que una nueva ejecución de Athena cambie el objetivo
        # contra el que se evalúa una actividad ya realizada.

        planned_training = None

        try:
            planned_training = await self.history.frozen_training_for_date(
                activity_date_str
            )

            if planned_training is not None:
                _LOGGER.debug(
                    "Coach AI DEBUG Garmin: PLAN DIARIO CONGELADO | fecha=%s | "
                    "workout=%s | duración=%s | TSS=%s",
                    activity_date_str,
                    planned_training.get("workout"),
                    planned_training.get("duration"),
                    planned_training.get("target_tss"),
                )

            # Compatibilidad: si no existe un plan congelado (por ejemplo,
            # actividades históricas anteriores a esta versión), usamos el
            # plan semanal o el historial antiguo como respaldo.
            if planned_training is None:
                today = dt_util.now().date()
                monday = today - timedelta(days=today.weekday())
                week_end = monday + timedelta(days=6)

                if weekly_plan and monday <= activity_date <= week_end:
                    day_index = (activity_date - monday).days
                    if 0 <= day_index < len(weekly_plan):
                        planned = weekly_plan[day_index]
                        if planned is not None:
                            planned_training = self._training_to_dict(planned)

                if planned_training is None:
                    planned_training = await self.history.training_for_date(
                        activity_date_str
                    )

        except Exception:
            _LOGGER.exception(
                "Error buscando el entrenamiento planificado para %s.",
                activity_date_str,
            )
            return None

        # ========================================================
        # SIN ENTRENAMIENTO PLANIFICADO
        # ========================================================

        if not planned_training:

            _LOGGER.debug(
                "Coach AI DEBUG Garmin: "
                "SIN entrenamiento planificado para %s. "
                "Se registra como EXTRA.",
                activity_date_str,
            )

            await self._save_extra_activity(
                activity,
                activity_date,
                None,
            )

            return None

        # ========================================================
        # DÍA DE DESCANSO
        # ========================================================

        is_rest = self._is_rest_training(
            planned_training
        )

        _LOGGER.debug(
            "Coach AI DEBUG Garmin: "
            "entrenamiento=%s | is_rest=%s",
            planned_training.get(
                "workout"
            ),
            is_rest,
        )

        if is_rest:

            _LOGGER.debug(
                "Coach AI DEBUG Garmin: "
                "actividad %s realizada durante "
                "día de DESCANSO (%s). "
                "Se registra como EXTRA.",
                activity_id,
                activity_date_str,
            )

            saved = await self._save_extra_activity(
                activity,
                activity_date,
                planned_training,
            )

            _LOGGER.debug(
                "Coach AI DEBUG Garmin: "
                "_save_extra_activity() devolvió %s",
                saved,
            )

            return None

        # ========================================================
        # EVALUAR ENTRENAMIENTO PLANIFICADO
        # ========================================================

        # WorkoutEvaluator trabaja con TrainingPlan, mientras que
        # planned_training se mantiene como dict en esta parte del
        # coordinator para facilitar el historial y la lógica semanal.
        # Convertimos aquí sin perder los intervalos.
        training_for_evaluation = None

        try:
            if isinstance(planned_training, TrainingPlan):
                training_for_evaluation = planned_training

            elif isinstance(planned_training, dict):
                serialized_intervals = planned_training.get(
                    "intervals",
                    [],
                )

                intervals = []

                if isinstance(serialized_intervals, list):
                    for item in serialized_intervals:
                        if not isinstance(item, dict):
                            continue

                        intervals.append(
                            Interval(
                                name=item.get("name") or "Intervalo",
                                duration=int(item.get("duration") or 0),
                                power=item.get("target_power"),
                                heart_rate=item.get("target_hr"),
                                cadence=item.get("cadence"),
                                step_type=item.get(
                                    "step_type",
                                    "interval",
                                ),
                                intensity=item.get(
                                    "intensity",
                                    "active",
                                ),
                            )
                        )

                training_for_evaluation = TrainingPlan(
                    workout=planned_training.get("workout") or "Unknown",
                    duration=int(planned_training.get("duration") or 0),
                    zone=planned_training.get("zone"),
                    target_power=planned_training.get("target_power"),
                    target_hr=planned_training.get("target_hr"),
                    cadence=planned_training.get("cadence"),
                    target_tss=planned_training.get("target_tss"),
                    intensity_factor=planned_training.get(
                        "intensity_factor"
                    ),
                    outdoor=planned_training.get("outdoor", False),
                    reason=planned_training.get("reason") or "",
                    intervals=intervals,
                    export=planned_training.get("export", {}),
                )

            if training_for_evaluation is None:
                _LOGGER.debug(
                    "Coach AI DEBUG Garmin: no se pudo convertir "
                    "el entrenamiento planificado a TrainingPlan | "
                    "tipo=%s | datos=%r",
                    type(planned_training).__name__,
                    planned_training,
                )
                return None

            _LOGGER.debug(
                "Coach AI DEBUG Garmin: TRAINING PARA EVALUACIÓN | "
                "tipo=%s | workout=%s | duración=%s | TSS=%s | "
                "intervalos=%s",
                type(training_for_evaluation).__name__,
                training_for_evaluation.workout,
                training_for_evaluation.duration,
                training_for_evaluation.target_tss,
                len(training_for_evaluation.intervals),
            )

            evaluation = (
                self.workout_evaluator.evaluate_real(
                    training_for_evaluation,
                    activity,
                )
            )

        except Exception:

            _LOGGER.exception(
                "Error evaluando actividad Garmin %s.",
                activity_id,
            )

            return None

        _LOGGER.debug(
            "Coach AI DEBUG Garmin: EVALUACIÓN | "
            "estado=%s | score=%.1f | cumplimiento=%.1f%% | "
            "duración=%s/%s | TSS=%s/%s",
            evaluation.status,
            evaluation.score,
            evaluation.completion_percent,
            evaluation.duration_real,
            evaluation.duration_target,
            evaluation.tss_real,
            evaluation.tss_target,
        )

        _LOGGER.info(
            "Coach AI - actividad Garmin %s evaluada: "
            "estado=%s score=%.1f completion=%.1f%%",
            activity_id,
            evaluation.status,
            evaluation.score,
            evaluation.completion_percent,
        )

        # --------------------------------------------------------
        # GUARDAR EJECUCIÓN
        # --------------------------------------------------------

        try:

            saved = await self.history.mark_completed(
                activity_date=activity_date_str,
                activity_id=activity.activity_id,
                activity_name=activity.activity_name,
                activity_type=activity.activity_type,
                start_time=activity.start_time,
                score=evaluation.score,
                duration_real=evaluation.duration_real,
                tss_real=evaluation.tss_real,
                power_real=evaluation.power_real,
                heart_rate_real=evaluation.heart_rate_real,
                completion_percent=(
                    evaluation.completion_percent
                ),
                feedback=evaluation.feedback,
            )

        except Exception:

            _LOGGER.exception(
                "Error guardando la evaluación "
                "de la actividad Garmin %s.",
                activity_id,
            )

            return None

        if not saved:

            _LOGGER.warning(
                "Coach AI - no se pudo guardar "
                "la evaluación de la actividad Garmin %s.",
                activity_id,
            )

            return None

        return evaluation

    # ============================================================
    # SEMANA / EJECUCIÓN
    # ============================================================

    def _build_weekly_execution(
        self,
        weekly_plan: list[Any],
        history_records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Construye la ejecución de lunes a domingo."""

        today = dt_util.now().date()

        # Semana de lunes a domingo.
        monday = today - timedelta(
            days=today.weekday()
        )

        day_names = [
            "lunes",
            "martes",
            "miércoles",
            "jueves",
            "viernes",
            "sábado",
            "domingo",
        ]

        weekly_execution: list[
            dict[str, Any]
        ] = []

        # ========================================================
        # RECORRER LOS 7 DÍAS
        # ========================================================

        for index in range(7):

            current_date = (
                monday
                + timedelta(days=index)
            )

            # ----------------------------------------------------
            # PLAN DEL DÍA
            # ----------------------------------------------------

            planned = None

            if (
                weekly_plan
                and index < len(weekly_plan)
            ):
                planned = weekly_plan[index]

            planned_workout = None
            planned_duration = None
            planned_tss = None
            planned_zone = None
            planned_power = None
            planned_hr = None
            planned_cadence = None
            planned_reason = None

            if planned is not None:

                planned_workout = getattr(
                    planned,
                    "workout",
                    None,
                )

                planned_duration = getattr(
                    planned,
                    "duration",
                    None,
                )

                planned_tss = getattr(
                    planned,
                    "target_tss",
                    None,
                )

                planned_zone = getattr(
                    planned,
                    "zone",
                    None,
                )

                planned_power = getattr(
                    planned,
                    "target_power",
                    None,
                )

                planned_hr = getattr(
                    planned,
                    "target_hr",
                    None,
                )

                planned_cadence = getattr(
                    planned,
                    "cadence",
                    None,
                )

                planned_reason = getattr(
                    planned,
                    "reason",
                    None,
                )

            # Compatibilidad con posibles nombres alternativos.
            if (
                planned_duration is None
                and planned is not None
            ):

                planned_duration = getattr(
                    planned,
                    "target_duration",
                    None,
                )

            if (
                planned_tss is None
                and planned is not None
            ):

                planned_tss = getattr(
                    planned,
                    "tss",
                    None,
                )

            # ----------------------------------------------------
            # BUSCAR EJECUCIÓN REAL
            # ----------------------------------------------------

            execution = None

            for record in reversed(
                history_records
            ):

                record_date = record.get(
                    "date"
                )

                if not record_date:
                    continue

                if isinstance(
                    record_date,
                    str,
                ):

                    normalized_date = (
                        record_date[:10]
                    )

                else:

                    normalized_date = (
                        str(record_date)[:10]
                    )

                if (
                    normalized_date
                    != current_date.isoformat()
                ):
                    continue

                if (
                    record.get("type")
                    != "athena_analysis"
                ):
                    continue

                possible_execution = (
                    record.get(
                        "execution"
                    )
                )

                if not isinstance(
                    possible_execution,
                    dict,
                ):
                    continue

                if (
                    possible_execution.get(
                        "activity_id"
                    )
                    is None
                ):
                    continue

                execution = (
                    possible_execution
                )

                break

            # ----------------------------------------------------
            # DATOS REALES
            # ----------------------------------------------------

            activity_id = None
            activity_name = None
            activity_type = None
            start_time = None

            actual_duration = None
            actual_tss = None
            actual_power = None
            actual_hr = None

            score = None
            completion = None
            feedback = None

            execution_status = None

            if execution:

                activity_id = execution.get(
                    "activity_id"
                )

                activity_name = execution.get(
                    "activity_name"
                )

                activity_type = execution.get(
                    "activity_type"
                )

                start_time = execution.get(
                    "start_time"
                )

                actual_duration = execution.get(
                    "duration_real"
                )

                actual_tss = execution.get(
                    "tss_real"
                )

                actual_power = execution.get(
                    "power_real"
                )

                actual_hr = execution.get(
                    "heart_rate_real"
                )

                score = execution.get(
                    "score"
                )

                completion = execution.get(
                    "completion_percent"
                )

                feedback = execution.get(
                    "feedback"
                )

                # El estado real de la ejecución se guarda actualmente
                # en record["status"] dentro de HistoryManager.
                # Algunas versiones antiguas no lo duplican en
                # execution["status"], por lo que debemos usar el estado
                # del registro como fuente de respaldo.
                execution_status = str(
                    execution.get(
                        "status"
                    )
                    or record.get(
                        "status"
                    )
                    or "NOT_COMPLETED"
                ).upper()

                _LOGGER.debug(
                    "Coach AI DEBUG Garmin: "
                    "ESTADO EJECUCIÓN | fecha=%s | activity_id=%s | "
                    "execution_status=%s | record_status=%s | "
                    "completion=%s",
                    current_date.isoformat(),
                    activity_id,
                    execution_status,
                    record.get("status"),
                    completion,
                )

            # ----------------------------------------------------
            # DETERMINAR DESCANSO
            # ----------------------------------------------------

            workout_text = str(
                planned_workout or ""
            ).strip().lower()

            is_rest = workout_text in {
                "rest",
                "descanso",
            }

            # Recovery NO se considera descanso.
            if workout_text in {
                "recovery",
                "recuperación",
                "recuperacion",
            }:

                is_rest = False

            # ====================================================
            # NORMALIZAR DESCANSO REAL
            # ====================================================
            # Si el entrenamiento es Rest/Descanso, nunca debe
            # conservar datos de una sesión anterior.
            if is_rest:
                if (
                    planned_duration not in (None, 0)
                    or planned_tss not in (None, 0)
                    or planned_power is not None
                    or planned_hr is not None
                    or planned_cadence is not None
                    or planned_zone not in (None, "REST", "rest")
                ):
                    _LOGGER.debug(
                        "Coach AI DEBUG WEEKLY: REST inconsistente | "
                        "fecha=%s | día=%s | duración=%s | TSS=%s | "
                        "potencia=%s | FC=%s | cadencia=%s | zona=%s. "
                        "Se normaliza a descanso real.",
                        current_date.isoformat(),
                        day_names[index],
                        planned_duration,
                        planned_tss,
                        planned_power,
                        planned_hr,
                        planned_cadence,
                        planned_zone,
                    )

                planned_duration = 0
                planned_tss = 0
                planned_zone = "REST"
                planned_power = None
                planned_hr = None
                planned_cadence = None

            # ====================================================
            # ESTADO
            # ====================================================

            # ----------------------------------------------------
            # ACTIVIDAD EXTRA
            # ----------------------------------------------------

            if (
                execution
                and execution_status == "EXTRA"
            ):

                status = "EXTRA"
                label = "🔵 NO PLANIFICADA"

            # ----------------------------------------------------
            # DESCANSO
            # ----------------------------------------------------

            elif is_rest:

                status = "REST"
                label = "⚪ DESCANSO"

            # ----------------------------------------------------
            # ENTRENAMIENTO EJECUTADO
            # ----------------------------------------------------

            elif execution:

                if execution_status == "COMPLETED":

                    status = "COMPLETED"
                    label = "🟢 REALIZADA"

                elif execution_status == "PARTIAL":

                    status = "PARTIAL"
                    label = "🟡 PARCIAL"

                else:

                    status = "NOT_COMPLETED"
                    label = "🔴 NO REALIZADA"

            # ----------------------------------------------------
            # DÍA PASADO
            # ----------------------------------------------------

            elif current_date < today:

                status = "MISSED"
                label = "🔴 NO REALIZADA"

            # ----------------------------------------------------
            # HOY / FUTURO
            # ----------------------------------------------------

            else:

                status = "PLANNED"
                label = "🟠 PLANIFICADA"

            # ----------------------------------------------------
            # NORMALIZAR SCORE
            # ----------------------------------------------------

            if score is not None:

                try:

                    score = round(
                        float(score),
                        1,
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    score = None

            # ----------------------------------------------------
            # NORMALIZAR COMPLETION
            # ----------------------------------------------------

            if completion is not None:

                try:

                    completion = round(
                        float(completion),
                        1,
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    completion = None

            # ----------------------------------------------------
            # RESULTADO DEL DÍA
            # ----------------------------------------------------

            weekly_execution.append(
                {
                    "date": current_date.isoformat(),

                    "day": day_names[index],

                    "planned": {
                        "workout": planned_workout,
                        "duration": planned_duration,
                        "tss": planned_tss,
                        "zone": planned_zone,
                        "power": planned_power,
                        "heart_rate": planned_hr,
                        "cadence": planned_cadence,
                        "reason": planned_reason,
                    },

                    "execution": {
                        "activity_id": activity_id,
                        "activity_name": activity_name,
                        "activity_type": activity_type,
                        "start_time": start_time,
                        "duration": actual_duration,
                        "tss": actual_tss,
                        "power": actual_power,
                        "heart_rate": actual_hr,
                        "score": score,
                        "completion_percent": completion,
                        "feedback": feedback,
                    },

                    "status": status,

                    "label": label,
                }
            )

        return weekly_execution

    # ============================================================
    # FIRMA DEL ESTADO
    # ============================================================

    @staticmethod
    def _build_signature(
        athlete: Any,
        weekly_tss: float,
        monthly_tss: float,
        unavailable_days: set[int],
        requested_rest_days: set[int],
        requested_training_days: set[int],
    ) -> tuple:
        """Genera una firma para detectar cambios."""

        return (
            athlete.body_battery,
            athlete.sleep_score,
            athlete.training_readiness,
            athlete.stress,
            athlete.hrv_status,
            athlete.resting_hr,
            athlete.vo2max,
            athlete.weight,
            athlete.ftp,
            athlete.ctl,
            athlete.atl,
            athlete.tsb,
            weekly_tss,
            monthly_tss,
            tuple(sorted(unavailable_days)),
            tuple(sorted(requested_rest_days)),
            tuple(sorted(requested_training_days)),
        )

    # ============================================================
    # ACTUALIZACIÓN PRINCIPAL
    # ============================================================

    async def _async_update_data(
        self,
    ) -> dict[str, Any]:
        """Actualiza todos los datos de Coach AI."""

        try:

            # ====================================================
            # ESTADO ACTUAL DEL ATLETA
            # ====================================================

            athlete = self.builder.build()

            if athlete is None:

                raise UpdateFailed(
                    "AthleteBuilder no ha devuelto "
                    "un AthleteState válido."
                )

            # ====================================================
            # HISTORIAL
            # ====================================================

            history_records = (
                await self.history.load()
            )

            await self._restore_ftp_test_result(history_records)

            # ====================================================
            # CARGA
            # ====================================================

            athlete = (
                self.load_engine.calculate(
                    athlete,
                    history_records,
                )
            )

            if athlete is None:

                raise UpdateFailed(
                    "LoadEngine no ha devuelto "
                    "un AthleteState válido."
                )

            # ====================================================
            # TSS SEMANAL
            # ====================================================

            weekly_tss = (
                self._calculate_period_tss(
                    history_records,
                    days=7,
                )
            )

            # ====================================================
            # TSS MENSUAL
            # ====================================================

            monthly_tss = (
                self._calculate_period_tss(
                    history_records,
                    days=30,
                )
            )

            athlete.weekly_tss = (
                weekly_tss
            )

            athlete.monthly_tss = (
                monthly_tss
            )

            # ====================================================
            # OBJETIVO
            # ====================================================

            goal = self.hass.states.get(
                "input_select.coach_ai_goal"
            )

            if goal is not None:

                athlete.goal = goal.state

            # ====================================================
            # DÍAS NO DISPONIBLES
            # ====================================================

            (
                unavailable_days,
                requested_rest_days,
                requested_training_days,
                day_preferences,
            ) = self._get_day_preferences()

            _LOGGER.debug(
                "Coach AI - preferencias de días: %s | no disponibles: %s | descansos: %s | entrenamientos: %s",
                day_preferences,
                sorted(unavailable_days),
                sorted(requested_rest_days),
                sorted(requested_training_days),
            )

            # ====================================================
            # ATHENA
            # ====================================================

            athena = self.athena.analyse(
                athlete,
                history_records,
                unavailable_days=unavailable_days,
                requested_rest_days=requested_rest_days,
                requested_training_days=requested_training_days,
            )

            # ====================================================
            # PLAN DIARIO CONGELADO
            # ====================================================

            frozen_today, frozen_record, daily_plan_changed = (
                await self._prepare_daily_plan(
                    athena,
                    unavailable_days,
                    requested_rest_days,
                    requested_training_days,
                )
            )

            # El día actual se sustituye en la semana de Athena por el
            # entrenamiento congelado. Los días futuros siguen pudiendo
            # adaptarse a los nuevos datos de recuperación.
            effective_week = list(getattr(athena, "week", None) or [])
            today_index = dt_util.now().date().weekday()
            if frozen_today is not None:
                while len(effective_week) <= today_index:
                    effective_week.append(None)
                effective_week[today_index] = frozen_today

            # ====================================================
            # FIRMA
            # ====================================================

            signature = (
                self._build_signature(
                    athlete,
                    weekly_tss,
                    monthly_tss,
                    unavailable_days,
                    requested_rest_days,
                    requested_training_days,
                )
            )

            fit_file = None

            # ====================================================
            # GUARDAR NUEVO ANÁLISIS
            # ====================================================

            if (
                signature
                != self._last_signature
                or daily_plan_changed
            ):
                await self.history.save(
                    athlete,
                    athena,
                )

                self._last_signature = signature

                _LOGGER.debug(
                    "Coach AI: análisis guardado; el plan de hoy permanece congelado."
                )

            # ----------------------------------------------------
            # FIT + GARMIN DEL PLAN CONGELADO
            # ----------------------------------------------------

            if frozen_today is not None:
                should_sync_garmin = False
                garmin_state = (
                    frozen_record.get("garmin", {})
                    if isinstance(frozen_record, dict)
                    else {}
                )

                if not isinstance(garmin_state, dict):
                    garmin_state = {}

                workout_key = str(getattr(frozen_today, "workout", "") or "").strip().lower()
                is_non_workout = workout_key in {
                    "rest",
                    "descanso",
                    "unavailable",
                    "no disponible",
                }

                if not garmin_state.get("scheduled") and not garmin_state.get("skipped"):
                    should_sync_garmin = not is_non_workout

                # Si el usuario ha forzado un recálculo, el estado Garmin
                # del nuevo registro empieza vacío. Aun así, REST/UNAVAILABLE
                # nunca se deben enviar a Garmin.
                if daily_plan_changed:
                    should_sync_garmin = not is_non_workout

                if is_non_workout:
                    # Al pasar explícitamente a Descanso/No disponible, retirar
                    # del calendario el evento anterior si podemos identificarlo
                    # sin ambigüedad. Nunca se borra la plantilla del entrenamiento.
                    old_workout_id = (
                        garmin_state.get("previous_workout_id")
                        or garmin_state.get("workout_id")
                    )
                    if old_workout_id and (
                        garmin_state.get("replacement_pending")
                        or garmin_state.get("scheduled")
                        or garmin_state.get("previous_scheduled")
                    ):
                        try:
                            async with GarminMCPClient() as client:
                                entries = extract_records(
                                    await client.get_scheduled_workouts(
                                        dt_util.now().date().isoformat(),
                                        dt_util.now().date().isoformat(),
                                    )
                                )
                                matches = []
                                for entry in entries:
                                    event_workout_id = entry.get("workout_id", entry.get("workoutId"))
                                    event_date = entry.get("calendar_date", entry.get("date", entry.get("scheduled_date")))
                                    event_id = entry.get("scheduled_workout_id", entry.get("scheduledWorkoutId"))
                                    if (
                                        str(event_workout_id) == str(old_workout_id)
                                        and event_id is not None
                                        and (not event_date or str(event_date)[:10] == dt_util.now().date().isoformat())
                                    ):
                                        matches.append(int(event_id))
                                if len(matches) == 1:
                                    await client.unschedule_workout(matches[0])
                                    _LOGGER.info(
                                        "Coach AI Garmin: sesión antigua retirada al marcar %s | fecha=%s | scheduled_workout_id=%s | workout_id=%s",
                                        getattr(frozen_today, "workout", "No disponible"),
                                        dt_util.now().date(), matches[0], old_workout_id,
                                    )
                                    await self.history.update_frozen_garmin(
                                        dt_util.now().date().isoformat(),
                                        scheduled=False,
                                        uploaded=False,
                                        skipped=True,
                                        reason="rest_or_unavailable",
                                        replacement_pending=False,
                                        workout_id=None,
                                        workout_signature=None,
                                        scheduled_workout_id=None,
                                        previous_scheduled=False,
                                    )
                                elif matches:
                                    _LOGGER.error(
                                        "Coach AI Garmin: no se retira sesión antigua; hay %s eventos coincidentes para %s.",
                                        len(matches), dt_util.now().date(),
                                    )
                                else:
                                    _LOGGER.warning(
                                        "Coach AI Garmin: no se encontró el evento antiguo para workout_id=%s en %s; no se ha borrado ninguna plantilla.",
                                        old_workout_id, dt_util.now().date(),
                                    )
                        except Exception as err:
                            _LOGGER.warning(
                                "Coach AI Garmin: error retirando sesión anterior para día no disponible/descanso: %s",
                                err,
                            )
                    await self.history.update_frozen_garmin(
                        dt_util.now().date().isoformat(),
                        skipped=True,
                        reason="rest_or_unavailable",
                    )
                elif should_sync_garmin:
                    synced, uploaded, scheduled = await self._sync_training_to_garmin(
                        frozen_today,
                        dt_util.now().date(),
                        existing_garmin=garmin_state,
                        force_replacement=(
                            isinstance(frozen_record, dict)
                            and frozen_record.get("source") in {"manual", "preference_change"}
                        ),
                    )
                    if synced:
                        workout_id = GarminMCPClient.extract_workout_id(uploaded)
                        await self.history.update_frozen_garmin(
                            dt_util.now().date().isoformat(),
                            workout_id=workout_id,
                            scheduled=True,
                            uploaded=True,
                            scheduled_date=dt_util.now().date().isoformat(),
                            uploaded_result=str(uploaded)[:2000],
                            scheduled_result=str(scheduled)[:2000],
                            synced_at=dt_util.now().isoformat(),
                            replacement_pending=False,
                        )
                        frozen_record = await self.history.frozen_plan_record_for_date(
                            dt_util.now().date().isoformat()
                        )

                # ------------------------------------------------
                # FIT: solo para entrenamientos reales.
                # En REST / NO DISPONIBLE no se genera FIT.
                # ------------------------------------------------
                if not is_non_workout:
                    try:
                        fit_file = self.workout_exporter.save_fit(
                            frozen_today
                        )
                    except Exception:
                        _LOGGER.exception(
                            "Error generando archivo FIT del plan congelado."
                        )
                        fit_file = None
                else:
                    fit_file = None
                    _LOGGER.debug(
                        "Coach AI: %s -> no se genera FIT.",
                        frozen_today.workout,
                    )

            # ----------------------------------------------------
            # NOTIFICACIÓN DIARIA: UNA VEZ DESDE LAS 09:00
            # ----------------------------------------------------

            now_local = dt_util.now()
            today_str = now_local.date().isoformat()

            if (
                frozen_today is not None
                and now_local.hour >= 9
                and not await self.history.notification_sent(today_str, "daily")
            ):
                try:
                    notification_data = {}
                    if not is_non_workout:
                        notification_data = {
                            "actions": [
                                {
                                    "action": "URI",
                                    "title": "📥 Descargar FIT",
                                    "uri": (
                                        "/local/coach_ai/"
                                        f"{frozen_today.workout.lower().replace(' ', '_')}.fit"
                                    ),
                                },
                            ],
                        }

                    sent = await self.notifier.send(
                        "🧠 Coach AI",
                        (
                            f"Workout: {frozen_today.workout}\n"
                            f"Duración: {frozen_today.duration} min\n"
                            f"TSS: {frozen_today.target_tss}\n"
                            f"Zona: {frozen_today.zone}"
                        ),
                        data=notification_data,
                    )

                    if sent:
                        await self.history.mark_notification_sent(
                            today_str,
                            "daily",
                        )
                except Exception:
                    _LOGGER.exception("Error enviando notificación diaria de Coach AI.")

            # ----------------------------------------------------
            # NOTIFICACIÓN EXTRA AL PULSAR "RECALCULAR SEMANA"
            # ----------------------------------------------------

            if (
                daily_plan_changed
                and isinstance(frozen_record, dict)
                and frozen_record.get("source") == "manual"
                and frozen_today is not None
            ):
                try:
                    notification_data = {}
                    if not is_non_workout:
                        notification_data = {
                            "actions": [
                                {
                                    "action": "URI",
                                    "title": "📥 Descargar FIT",
                                    "uri": (
                                        "/local/coach_ai/"
                                        f"{frozen_today.workout.lower().replace(' ', '_')}.fit"
                                    ),
                                },
                            ],
                        }

                    await self.notifier.send(
                        "🔄 Coach AI · Semana recalculada",
                        (
                            f"Nuevo workout de hoy: {frozen_today.workout}\n"
                            f"Duración: {frozen_today.duration} min\n"
                            f"TSS: {frozen_today.target_tss}\n"
                            f"Zona: {frozen_today.zone}"
                        ),
                        data=notification_data,
                    )
                except Exception:
                    _LOGGER.exception(
                        "Error enviando notificación de recálculo de Coach AI."
                    )

            # ====================================================
            # ACTIVIDAD REAL DE GARMIN
            # ====================================================

            try:

                last_activity = (
                    await self.hass.async_add_executor_job(
                        self.activity_engine.analyse
                    )
                )

            except Exception:

                _LOGGER.exception(
                    "Error analizando la "
                    "última actividad Garmin."
                )

                last_activity = None

            # ----------------------------------------------------
            # DEBUG ACTIVIDAD OBTENIDA
            # ----------------------------------------------------

            _LOGGER.debug(
                "Coach AI DEBUG Garmin: "
                "ActivityEngine.analyse() -> %s",
                last_activity,
            )

            # ====================================================
            # EVALUAR ACTIVIDAD REAL
            # ====================================================

            workout_evaluation = None

            if last_activity is not None:

                _LOGGER.debug(
                    "Coach AI DEBUG Garmin: "
                    "procesando última actividad."
                )

                try:

                    workout_evaluation = (
                        await self._evaluate_last_activity(
                            last_activity,
                            weekly_plan=effective_week,
                        )
                    )

                except Exception:

                    _LOGGER.exception(
                        "Error evaluando la "
                        "última actividad Garmin."
                    )

            else:

                _LOGGER.debug(
                    "Coach AI DEBUG Garmin: "
                    "NO hay actividad para procesar."
                )

            # ====================================================
            # ANALIZAR TEST FTP
            # ====================================================

            try:
                await self._analyse_ftp_test_activity(
                    last_activity,
                    athlete=athlete,
                    athena=athena,
                )
            except Exception:
                _LOGGER.exception(
                    "Coach AI FTP: error en el análisis automático del test."
                )

            try:
                await self._maybe_schedule_ftp_test()
            except Exception:
                _LOGGER.exception(
                    "Coach AI FTP: error en el ciclo automático de 6 semanas."
                )

            # ====================================================
            # RECARGAR HISTORIAL
            # ====================================================

            if last_activity is not None:

                try:

                    history_records = (
                        await self.history.load()
                    )

                    _LOGGER.debug(
                        "Coach AI DEBUG Garmin: "
                        "historial recargado tras "
                        "procesar actividad. registros=%s",
                        len(history_records),
                    )

                except Exception:

                    _LOGGER.exception(
                        "Error recargando historial "
                        "después de procesar actividad."
                    )

            # ====================================================
            # HISTORIAL DE CARGA
            # ====================================================

            try:

                load_history = (
                    self.load_engine.build_series(
                        history_records,
                        days=30,
                    )
                )

            except Exception:

                _LOGGER.exception(
                    "Error generando historial "
                    "de carga."
                )

                load_history = []

            # ====================================================
            # EJECUCIÓN SEMANAL
            # ====================================================

            try:

                weekly_execution = (
                    self._build_weekly_execution(
                        effective_week,
                        history_records,
                    )
                )

                _LOGGER.debug(
                    "Coach AI DEBUG Garmin: "
                    "weekly_execution construido: %s",
                    weekly_execution,
                )

            except Exception:

                _LOGGER.exception(
                    "Error construyendo "
                    "weekly_execution."
                )

                weekly_execution = []

            # ====================================================
            # RESULTADO
            # ====================================================

            return {
                # ------------------------------------------------
                # ATLETA
                # ------------------------------------------------

                "athlete": athlete,

                # ------------------------------------------------
                # ATHENA
                # ------------------------------------------------

                "athena": athena,

                # ------------------------------------------------
                # TEST FTP
                # ------------------------------------------------

                "ftp_test": dict(self._ftp_test_result),

                # ------------------------------------------------
                # FIT
                # ------------------------------------------------

                "fit_file": fit_file,

                # ------------------------------------------------
                # GARMIN
                # ------------------------------------------------

                "last_activity": (
                    last_activity
                ),

                "workout_evaluation": (
                    workout_evaluation
                ),

                # ------------------------------------------------
                # HISTORIAL
                # ------------------------------------------------

                "history_records": (
                    len(history_records)
                ),

                "last_analysis": (
                    await self.history.last()
                ),

                # ------------------------------------------------
                # CARGA
                # ------------------------------------------------

                "ctl": athlete.ctl,

                "atl": athlete.atl,

                "tsb": athlete.tsb,

                # ------------------------------------------------
                # TSS
                # ------------------------------------------------

                "weekly_tss": weekly_tss,

                "monthly_tss": monthly_tss,

                # ------------------------------------------------
                # HISTORIAL DE CARGA
                # ------------------------------------------------

                "load_history": load_history,

                # ------------------------------------------------
                # SEMANA
                # ------------------------------------------------

                "week": effective_week,

                # ------------------------------------------------
                # DISPONIBILIDAD
                # ------------------------------------------------

                "unavailable_days": sorted(
                    unavailable_days
                ),

                # ------------------------------------------------
                # EJECUCIÓN SEMANAL
                # ------------------------------------------------

                "weekly_execution": (
                    weekly_execution
                ),
            }

        except UpdateFailed:

            raise

        except Exception as err:

            _LOGGER.exception(
                "Error actualizando Coach AI"
            )

            raise UpdateFailed(
                f"Error actualizando Coach AI: {err}"
            ) from err