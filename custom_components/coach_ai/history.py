"""Gestor del historial de Coach AI."""

from __future__ import annotations

from datetime import date, datetime
import json
import logging
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant


_LOGGER = logging.getLogger(__name__)


class HistoryManager:
    """Gestiona el historial persistente de Coach AI."""

    MAX_RECORDS = 365

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Inicializa el gestor."""

        self.hass = hass

        self.file_path = Path(
            hass.config.path(
                "coach_ai_history.json"
            )
        )

    # ============================================================
    # SERIALIZACIÓN
    # ============================================================

    @staticmethod
    def _json_serializer(
        obj: Any,
    ) -> str:
        """Convierte objetos especiales a JSON."""

        if isinstance(
            obj,
            (
                datetime,
                date,
            ),
        ):
            return obj.isoformat()

        if hasattr(
            obj,
            "isoformat",
        ):
            return obj.isoformat()

        raise TypeError(
            f"Object of type "
            f"{type(obj).__name__} "
            f"is not JSON serializable"
        )

    # ============================================================
    # CARGAR HISTORIAL
    # ============================================================

    def _load_sync(
        self,
    ) -> list[dict[str, Any]]:
        """Carga el historial desde disco."""

        if not self.file_path.exists():
            return []

        try:

            with self.file_path.open(
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(file)

            if not isinstance(
                data,
                list,
            ):
                _LOGGER.warning(
                    "El historial de Coach AI "
                    "no contiene una lista válida."
                )
                return []

            return data

        except (
            json.JSONDecodeError,
            OSError,
            TypeError,
            ValueError,
        ) as err:

            _LOGGER.error(
                "No se pudo cargar el historial: %s",
                err,
            )

            # ----------------------------------------------------
            # HACER COPIA DEL ARCHIVO CORRUPTO
            # ----------------------------------------------------

            try:

                corrupt_path = (
                    self.file_path.with_name(
                        "coach_ai_history.corrupt.json"
                    )
                )

                if not corrupt_path.exists():

                    self.file_path.replace(
                        corrupt_path
                    )

                    _LOGGER.warning(
                        "Historial corrupto movido a: %s",
                        corrupt_path,
                    )

            except OSError as backup_err:

                _LOGGER.error(
                    "No se pudo hacer copia del "
                    "historial corrupto: %s",
                    backup_err,
                )

            return []

    async def load(
        self,
    ) -> list[dict[str, Any]]:
        """Carga el historial."""

        return await self.hass.async_add_executor_job(
            self._load_sync
        )

    # ============================================================
    # GUARDAR HISTORIAL
    # ============================================================

    def _save_sync(
        self,
        records: list[dict[str, Any]],
    ) -> None:
        """Guarda el historial de forma atómica."""

        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_path = (
            self.file_path.with_name(
                "coach_ai_history.tmp.json"
            )
        )

        try:

            # ----------------------------------------------------
            # ESCRIBIR TEMPORAL
            # ----------------------------------------------------

            with temp_path.open(
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    records,
                    file,
                    ensure_ascii=False,
                    indent=2,
                    default=self._json_serializer,
                )

                file.flush()

            # ----------------------------------------------------
            # VALIDAR
            # ----------------------------------------------------

            with temp_path.open(
                "r",
                encoding="utf-8",
            ) as file:

                json.load(file)

            # ----------------------------------------------------
            # REEMPLAZO ATÓMICO
            # ----------------------------------------------------

            temp_path.replace(
                self.file_path
            )

        except Exception:

            _LOGGER.exception(
                "No se pudo guardar el historial de Coach AI."
            )

            try:

                if temp_path.exists():
                    temp_path.unlink()

            except OSError:
                pass

            raise

    async def save_records(
        self,
        records: list[dict[str, Any]],
    ) -> None:
        """Guarda los registros."""

        await self.hass.async_add_executor_job(
            self._save_sync,
            records,
        )

    # ============================================================
    # GUARDAR ANÁLISIS DE ATHENA
    # ============================================================

    async def save(
        self,
        athlete,
        athena,
    ) -> None:
        """Guarda un análisis de Athena."""

        records = await self.load()

        now = datetime.now().astimezone()

        training = getattr(
            athena,
            "training",
            None,
        )

        # --------------------------------------------------------
        # ATLETA
        # --------------------------------------------------------

        athlete_data = {
            "body_battery": getattr(
                athlete,
                "body_battery",
                None,
            ),
            "sleep_score": getattr(
                athlete,
                "sleep_score",
                None,
            ),
            "training_readiness": getattr(
                athlete,
                "training_readiness",
                None,
            ),
            "stress": getattr(
                athlete,
                "stress",
                None,
            ),
            "hrv_status": getattr(
                athlete,
                "hrv_status",
                None,
            ),
            "resting_hr": getattr(
                athlete,
                "resting_hr",
                None,
            ),
            "vo2max": getattr(
                athlete,
                "vo2max",
                None,
            ),
            "weight": getattr(
                athlete,
                "weight",
                None,
            ),
            "ftp": getattr(
                athlete,
                "ftp",
                None,
            ),
            "ctl": getattr(
                athlete,
                "ctl",
                None,
            ),
            "atl": getattr(
                athlete,
                "atl",
                None,
            ),
            "tsb": getattr(
                athlete,
                "tsb",
                None,
            ),
            "weekly_tss": getattr(
                athlete,
                "weekly_tss",
                None,
            ),
            "monthly_tss": getattr(
                athlete,
                "monthly_tss",
                None,
            ),
            "goal": getattr(
                athlete,
                "goal",
                None,
            ),
        }

        # --------------------------------------------------------
        # ANÁLISIS
        # --------------------------------------------------------

        analysis_data = {
            "recovery_score": getattr(
                athena,
                "recovery_score",
                None,
            ),
            "recovery_level": getattr(
                athena,
                "recovery_level",
                None,
            ),
            "fitness_score": getattr(
                athena,
                "fitness_score",
                None,
            ),
            "fatigue_score": getattr(
                athena,
                "fatigue_score",
                None,
            ),
            "workout_score": getattr(
                athena,
                "workout_score",
                None,
            ),
            "workout_quality": getattr(
                athena,
                "workout_quality",
                None,
            ),
            "reasons": getattr(
                athena,
                "reasons",
                [],
            ),
        }

        # --------------------------------------------------------
        # ENTRENAMIENTO
        # --------------------------------------------------------

        training_data = None

        if training is not None:

            training_data = {
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
                "target_power": getattr(
                    training,
                    "target_power",
                    None,
                ),
                "target_hr": getattr(
                    training,
                    "target_hr",
                    None,
                ),
                "cadence": getattr(
                    training,
                    "cadence",
                    None,
                ),
                "target_tss": getattr(
                    training,
                    "target_tss",
                    None,
                ),
                "intensity_factor": getattr(
                    training,
                    "intensity_factor",
                    None,
                ),
                "outdoor": getattr(
                    training,
                    "outdoor",
                    None,
                ),
                "reason": getattr(
                    training,
                    "reason",
                    None,
                ),
            }

            # ----------------------------------------------------
            # INTERVALOS
            # ----------------------------------------------------

            intervals = getattr(
                training,
                "intervals",
                None,
            )

            if intervals is not None:

                serialized_intervals = []

                for interval in intervals:

                    if isinstance(
                        interval,
                        dict,
                    ):
                        serialized_intervals.append(
                            interval
                        )
                        continue

                    serialized_intervals.append(
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
                            "zone": getattr(
                                interval,
                                "zone",
                                None,
                            ),
                            "target_power": getattr(
                                interval,
                                "target_power",
                                None,
                            ),
                            "target_hr": getattr(
                                interval,
                                "target_hr",
                                None,
                            ),
                            "cadence": getattr(
                                interval,
                                "cadence",
                                None,
                            ),
                        }
                    )

                training_data[
                    "intervals"
                ] = serialized_intervals

        # --------------------------------------------------------
        # EJECUCIÓN
        # --------------------------------------------------------

        execution = {
            "activity_id": None,
            "activity_name": None,
            "activity_type": None,
            "start_time": None,
            "score": None,
            "duration_real": None,
            "tss_real": None,
            "power_real": None,
            "heart_rate_real": None,
            "cadence_real": None,
            "completion_percent": None,
            "feedback": None,
        }

        # --------------------------------------------------------
        # REGISTRO
        # --------------------------------------------------------

        record = {
            "timestamp": now.isoformat(),
            "date": now.date().isoformat(),
            "type": "athena_analysis",
            "status": (
                "planned"
                if training is not None
                else "analysis_only"
            ),
            "execution": execution,
            "athlete": athlete_data,
            "analysis": analysis_data,
            "training": training_data,
        }

        records.append(record)

        # --------------------------------------------------------
        # LIMITE
        # --------------------------------------------------------

        if len(records) > self.MAX_RECORDS:

            records = records[
                -self.MAX_RECORDS:
            ]

        await self.save_records(
            records
        )

        _LOGGER.debug(
            "Coach AI - análisis guardado "
            "en el historial."
        )

    # ============================================================
    # PLAN DIARIO CONGELADO
    # ============================================================

    @staticmethod
    def _serialize_training(training: Any) -> dict[str, Any] | None:
        """Serializa un TrainingPlan para conservarlo como plan diario."""
        if training is None:
            return None

        data: dict[str, Any] = {
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
        }

        intervals = getattr(training, "intervals", None)
        serialized_intervals: list[dict[str, Any]] = []

        if intervals:
            for interval in intervals:
                if isinstance(interval, dict):
                    serialized_intervals.append(interval)
                    continue

                serialized_intervals.append(
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

        data["intervals"] = serialized_intervals
        export = getattr(training, "export", None)
        if isinstance(export, dict):
            data["export"] = export

        return data

    async def frozen_training_for_date(
        self,
        activity_date: str,
    ) -> dict[str, Any] | None:
        """Devuelve el plan diario congelado, si existe."""
        records = await self.load()

        for record in reversed(records):
            if record.get("type") != "daily_plan":
                continue
            if str(record.get("date", ""))[:10] != str(activity_date)[:10]:
                continue

            training = record.get("training")
            if isinstance(training, dict):
                return training

        return None

    async def frozen_plan_record_for_date(
        self,
        activity_date: str,
    ) -> dict[str, Any] | None:
        """Devuelve el registro completo del plan diario congelado."""
        records = await self.load()

        for record in reversed(records):
            if record.get("type") != "daily_plan":
                continue
            if str(record.get("date", ""))[:10] != str(activity_date)[:10]:
                continue
            return record

        return None

    async def save_frozen_training(
        self,
        activity_date: str,
        training: Any,
        *,
        source: str = "daily",
        preference: str = "Athena",
        replace: bool = False,
    ) -> bool:
        """Guarda el entrenamiento que debe permanecer fijo ese día."""
        training_data = self._serialize_training(training)
        if training_data is None:
            return False

        records = await self.load()
        date_key = str(activity_date)[:10]

        existing_index = None
        existing_record = None
        for index in range(len(records) - 1, -1, -1):
            record = records[index]
            if record.get("type") != "daily_plan":
                continue
            if str(record.get("date", ""))[:10] != date_key:
                continue
            existing_index = index
            existing_record = record
            break

        if existing_record is not None and not replace:
            return False

        now = datetime.now().astimezone().isoformat()

        # Al sustituir el plan diario, conservar los identificadores y el
        # estado de Garmin. Si se reinicia Home Assistant o falla la
        # sincronización, el coordinador podrá reconocer la plantilla ya
        # creada y evitar subir otra idéntica.
        garmin_data: dict[str, Any] = {}
        if isinstance(existing_record, dict):
            previous_garmin = existing_record.get("garmin")
            if isinstance(previous_garmin, dict):
                garmin_data = dict(previous_garmin)

        record = {
            "timestamp": now,
            "date": date_key,
            "type": "daily_plan",
            "status": "planned",
            "source": source,
            "preference": preference,
            "training": training_data,
            "garmin": garmin_data,
        }

        if existing_index is not None:
            records[existing_index] = record
        else:
            records.append(record)

        if len(records) > self.MAX_RECORDS:
            records = records[-self.MAX_RECORDS:]

        await self.save_records(records)

        _LOGGER.info(
            "Coach AI - plan diario congelado | fecha=%s | workout=%s | source=%s | preference=%s",
            date_key,
            training_data.get("workout"),
            source,
            preference,
        )
        return True

    async def update_frozen_garmin(
        self,
        activity_date: str,
        **garmin_data: Any,
    ) -> bool:
        """Actualiza el estado de sincronización Garmin del plan diario."""
        records = await self.load()
        date_key = str(activity_date)[:10]

        for record in reversed(records):
            if record.get("type") != "daily_plan":
                continue
            if str(record.get("date", ""))[:10] != date_key:
                continue

            current = record.get("garmin")
            if not isinstance(current, dict):
                current = {}
                record["garmin"] = current

            current.update(garmin_data)
            record["garmin_updated"] = datetime.now().astimezone().isoformat()
            await self.save_records(records)
            return True

        return False

    async def notification_sent(
        self,
        notification_date: str,
        kind: str = "daily",
    ) -> bool:
        """Comprueba si una notificación concreta ya fue enviada."""
        records = await self.load()
        date_key = str(notification_date)[:10]

        return any(
            record.get("type") == "coach_ai_notification"
            and str(record.get("date", ""))[:10] == date_key
            and record.get("kind") == kind
            for record in records
        )

    async def mark_notification_sent(
        self,
        notification_date: str,
        kind: str = "daily",
    ) -> None:
        """Registra una notificación enviada para evitar duplicados."""
        records = await self.load()
        date_key = str(notification_date)[:10]

        records.append(
            {
                "timestamp": datetime.now().astimezone().isoformat(),
                "date": date_key,
                "type": "coach_ai_notification",
                "kind": kind,
            }
        )

        if len(records) > self.MAX_RECORDS:
            records = records[-self.MAX_RECORDS:]

        await self.save_records(records)

    # ============================================================
    # BUSCAR ENTRENAMIENTO POR FECHA
    # ============================================================

    async def training_for_date(
        self,
        activity_date: str,
    ) -> dict[str, Any] | None:
        """Obtiene el entrenamiento planificado de una fecha."""

        records = await self.load()

        for record in reversed(
            records
        ):

            if record.get(
                "type"
            ) != "athena_analysis":
                continue

            if record.get(
                "date"
            ) != activity_date:
                continue

            training = record.get(
                "training"
            )

            if not isinstance(
                training,
                dict,
            ):
                continue

            return training

        return None

    # ============================================================
    # COMPROBAR ACTIVIDAD EXISTENTE
    # ============================================================

    async def activity_exists(
        self,
        activity_id: int | str | None,
    ) -> bool:
        """Comprueba si una actividad Garmin ya fue procesada."""

        if activity_id is None:
            return False

        records = await self.load()

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
                return True

        return False

    # ============================================================
    # ACTUALIZAR POTENCIA DE UNA ACTIVIDAD YA PROCESADA
    # ============================================================

    async def update_activity_power(
        self,
        activity_id: int | str | None,
        power_real: int | float | None,
    ) -> bool:
        """Actualiza la potencia de una actividad ya existente.

        Se utiliza cuando Garmin publica posteriormente un dato de
        potencia que no estaba disponible en el primer procesamiento.
        No modifica TSS, duración, puntuación, estado ni feedback.
        """

        if activity_id is None or power_real is None:
            return False

        try:
            power_value = int(round(float(power_real)))
        except (TypeError, ValueError):
            return False

        if power_value <= 0:
            return False

        records = await self.load()
        activity_id_str = str(activity_id)
        updated = False

        for record in records:
            execution = record.get("execution")

            if not isinstance(execution, dict):
                continue

            stored_id = execution.get("activity_id")

            if stored_id is None or str(stored_id) != activity_id_str:
                continue

            current_power = execution.get("power_real")

            # Solo rellenamos el dato si estaba ausente o inválido.
            try:
                current_power_value = (
                    float(current_power)
                    if current_power is not None
                    else None
                )
            except (TypeError, ValueError):
                current_power_value = None

            if current_power_value is not None and current_power_value > 0:
                return False

            execution["power_real"] = power_value
            record["execution_updated"] = datetime.now().astimezone().isoformat()
            updated = True

            _LOGGER.info(
                "Coach AI - potencia actualizada para actividad Garmin %s "
                "| potencia=%s W",
                activity_id,
                power_value,
            )
            break

        if not updated:
            return False

        await self.save_records(records)
        return True

    # ============================================================
    # MARCAR COMPLETADO
    # ============================================================

    async def mark_completed(
        self,
        activity_date: str,
        activity_id: int | str | None = None,
        activity_name: str | None = None,
        activity_type: str | None = None,
        start_time: str | datetime | None = None,
        duration_real: int | None = None,
        tss_real: float | None = None,
        power_real: int | None = None,
        heart_rate_real: int | None = None,
        cadence_real: int | None = None,
        score: float | None = None,
        completion_percent: float | None = None,
        feedback: str | None = None,
    ) -> bool:
        """Asocia una actividad Garmin con el entrenamiento."""

        # --------------------------------------------------------
        # EVITAR DUPLICADOS
        # --------------------------------------------------------

        if activity_id is not None:

            if await self.activity_exists(
                activity_id
            ):

                _LOGGER.debug(
                    "Coach AI - actividad %s "
                    "ya existe.",
                    activity_id,
                )

                return False

        # --------------------------------------------------------
        # NORMALIZAR START TIME
        # --------------------------------------------------------

        if isinstance(
            start_time,
            (
                datetime,
                date,
            ),
        ):
            start_time = (
                start_time.isoformat()
            )

        # --------------------------------------------------------
        # CARGAR
        # --------------------------------------------------------

        records = await self.load()

        # --------------------------------------------------------
        # ACTUALIZAR
        # --------------------------------------------------------

        updated = self._update_execution(
            records=records,
            activity_date=activity_date,
            activity_id=activity_id,
            activity_name=activity_name,
            activity_type=activity_type,
            start_time=start_time,
            duration_real=duration_real,
            tss_real=tss_real,
            power_real=power_real,
            heart_rate_real=heart_rate_real,
            cadence_real=cadence_real,
            score=score,
            completion_percent=completion_percent,
            feedback=feedback,
        )

        if not updated:
            return False

        # --------------------------------------------------------
        # GUARDAR
        # --------------------------------------------------------

        await self.save_records(
            records
        )

        _LOGGER.info(
            "Coach AI - actividad Garmin %s "
            "guardada correctamente.",
            activity_id,
        )

        return True

    # ============================================================
    # ACTUALIZAR EJECUCIÓN
    # ============================================================

    def _update_execution(
        self,
        records: list[dict[str, Any]],
        activity_date: str,
        activity_id: int | str | None = None,
        activity_name: str | None = None,
        activity_type: str | None = None,
        start_time: str | None = None,
        duration_real: int | None = None,
        tss_real: float | None = None,
        power_real: int | None = None,
        heart_rate_real: int | None = None,
        cadence_real: int | None = None,
        score: float | None = None,
        completion_percent: float | None = None,
        feedback: str | None = None,
    ) -> bool:
        """Actualiza el entrenamiento con datos reales."""

        # --------------------------------------------------------
        # BUSCAR DESDE EL MÁS RECIENTE
        # --------------------------------------------------------

        for record in reversed(
            records
        ):

            if record.get(
                "type"
            ) != "athena_analysis":
                continue

            if record.get(
                "date"
            ) != activity_date:
                continue

            training = record.get(
                "training"
            )

            if not isinstance(
                training,
                dict,
            ):
                continue

            # ----------------------------------------------------
            # NO SOBRESCRIBIR SESIONES PROCESADAS
            # ----------------------------------------------------

            current_status = record.get(
                "status"
            )

            if current_status in {
                "completed",
                "partial",
                "not_completed",
            }:
                continue

            # Un registro marcado como "missed" todavía puede
            # recibir una actividad Garmin posterior, siempre que
            # no tenga ya una ejecución asociada.
            if current_status == "missed":
                execution = record.get("execution")

                if (
                    isinstance(execution, dict)
                    and execution.get("activity_id") is not None
                ):
                    continue

            # ----------------------------------------------------
            # EJECUCIÓN
            # ----------------------------------------------------

            execution = record.get(
                "execution"
            )

            if not isinstance(
                execution,
                dict,
            ):

                execution = {}

                record[
                    "execution"
                ] = execution

            execution[
                "activity_id"
            ] = activity_id

            execution[
                "activity_name"
            ] = activity_name

            execution[
                "activity_type"
            ] = activity_type

            execution[
                "start_time"
            ] = start_time

            execution[
                "score"
            ] = score

            execution[
                "duration_real"
            ] = duration_real

            execution[
                "tss_real"
            ] = tss_real

            execution[
                "power_real"
            ] = power_real

            execution[
                "heart_rate_real"
            ] = heart_rate_real

            execution[
                "cadence_real"
            ] = cadence_real

            execution[
                "completion_percent"
            ] = completion_percent

            execution[
                "feedback"
            ] = feedback

            # ----------------------------------------------------
            # ESTADO
            # ----------------------------------------------------

            if completion_percent is None:

                record[
                    "status"
                ] = "completed"

            elif completion_percent >= 85:

                record[
                    "status"
                ] = "completed"

            elif completion_percent >= 55:

                record[
                    "status"
                ] = "partial"

            else:

                record[
                    "status"
                ] = "not_completed"

            # ----------------------------------------------------
            # FECHA DE ACTUALIZACIÓN
            # ----------------------------------------------------

            record[
                "execution_updated"
            ] = (
                datetime.now()
                .astimezone()
                .isoformat()
            )

            _LOGGER.info(
                "Coach AI - entrenamiento del %s "
                "actualizado con Garmin %s | "
                "estado_anterior=%s | estado_nuevo=%s | "
                "cumplimiento=%.1f%% | duración=%s | TSS=%s",
                activity_date,
                activity_id,
                current_status,
                record["status"],
                completion_percent or 0,
                duration_real,
                tss_real,
            )

            return True

        _LOGGER.warning(
            "Coach AI - no se encontró un "
            "entrenamiento planificado pendiente "
            "para el %s.",
            activity_date,
        )

        return False

    # ============================================================
    # MARCAR NO REALIZADO
    # ============================================================

    async def mark_missed(
        self,
        activity_date: str,
    ) -> bool:
        """Marca como no realizado el entrenamiento."""

        records = await self.load()

        for record in reversed(
            records
        ):

            if record.get(
                "type"
            ) != "athena_analysis":
                continue

            if record.get(
                "date"
            ) != activity_date:
                continue

            training = record.get(
                "training"
            )

            if not isinstance(
                training,
                dict,
            ):
                continue

            if record.get(
                "status"
            ) in {
                "completed",
                "partial",
                "missed",
            }:
                return False

            record[
                "status"
            ] = "missed"

            await self.save_records(
                records
            )

            return True

        return False

    # ============================================================
    # ÚLTIMO REGISTRO
    # ============================================================

    async def last(
        self,
    ) -> dict[str, Any] | None:
        """Devuelve el último registro."""

        records = await self.load()

        if not records:
            return None

        return records[-1]

    # ============================================================
    # ÚLTIMO ENTRENAMIENTO
    # ============================================================

    async def last_training(
        self,
    ) -> dict[str, Any] | None:
        """Devuelve el último entrenamiento."""

        records = await self.load()

        for record in reversed(
            records
        ):

            training = record.get(
                "training"
            )

            if isinstance(
                training,
                dict,
            ):
                return training

        return None

    # ============================================================
    # SESIONES COMPLETADAS
    # ============================================================

    async def completed_sessions(
        self,
    ) -> list[dict[str, Any]]:
        """Devuelve las sesiones realizadas."""

        records = await self.load()

        return [
            record
            for record in records
            if record.get(
                "status"
            )
            in {
                "completed",
                "partial",
            }
        ]

    # ============================================================
    # CONTADOR
    # ============================================================

    async def count(
        self,
    ) -> int:
        """Devuelve el número de registros."""

        records = await self.load()

        return len(records)

    # ============================================================
    # LIMPIAR
    # ============================================================

    async def clear(
        self,
    ) -> None:
        """Limpia el historial."""

        await self.save_records([])

        _LOGGER.warning(
            "Coach AI - historial eliminado."
        )