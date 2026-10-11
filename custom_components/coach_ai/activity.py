"""Analizador de actividades reales de Garmin."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

from .models import ActivitySummary


_LOGGER = logging.getLogger(__name__)


class ActivityEngine:
    """Analiza la última actividad disponible de Garmin."""

    ENTITY_ID = "sensor.garmin_connect_last_activity"

    def __init__(
        self,
        hass: HomeAssistant,
    ) -> None:
        """Inicializa el motor."""

        self.hass = hass

    # ============================================================
    # CONVERSIONES
    # ============================================================

    @staticmethod
    def _float(
        value: Any,
    ) -> float | None:
        """Convierte un valor a float."""

        if value is None:
            return None

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _int(
        value: Any,
    ) -> int | None:
        """Convierte un valor a int."""

        if value is None:
            return None

        try:
            return int(float(value))

        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _duration_minutes(
        value: Any,
    ) -> int | None:
        """Convierte segundos a minutos."""

        seconds = ActivityEngine._float(value)

        if seconds is None:
            return None

        return max(
            0,
            round(seconds / 60),
        )

    @staticmethod
    def _parse_start_time(
        value: Any,
    ) -> datetime | str | None:
        """Normaliza startTime."""

        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        text = str(value).strip()

        if not text:
            return None

        try:
            return datetime.fromisoformat(
                text.replace("Z", "+00:00")
            )

        except ValueError:
            return text

    def _fit_estimated_average_power(
        self,
        activity_id: int | None,
    ) -> int | None:
        """Obtiene la potencia estimada Garmin (est_power) desde el FIT.

        Se utiliza únicamente como fallback cuando Garmin no expone
        avgPower/averagePower en los atributos de Home Assistant.
        """
        if activity_id is None:
            return None

        fit_path = Path(
            f"/config/garmin_activities/activity_{activity_id}.fit"
        )

        if not fit_path.is_file():
            _LOGGER.debug(
                "Coach AI Garmin: no existe FIT para activityId=%s: %s",
                activity_id,
                fit_path,
            )
            return None

        try:
            import fitdecode
        except ImportError:
            _LOGGER.warning(
                "Coach AI Garmin: fitdecode no está instalado; "
                "no se puede leer est_power del FIT."
            )
            return None

        values: list[float] = []
        estimated_summary: float | None = None

        try:
            with fitdecode.FitReader(str(fit_path)) as fit:
                for frame in fit:
                    if not isinstance(frame, fitdecode.FitDataMessage):
                        continue

                    # Garmin guarda en el mensaje Session un campo
                    # Developer/Connect IQ llamado "est_avg_pow".
                    # Este es el valor resumen que Garmin Connect muestra
                    # como "Estimated Avg Power" y es preferible a
                    # calcular nosotros la media de est_power.
                    for field in frame.fields:
                        if field.name == "est_avg_pow":
                            value = self._float(field.value)
                            if value is not None and value > 0:
                                estimated_summary = value
                                break

                    if estimated_summary is not None:
                        break

            if estimated_summary is not None:
                result = round(estimated_summary)

                _LOGGER.warning(
                    "Coach AI Garmin: potencia estimada FIT (resumen) | "
                    "activityId=%s | campo=est_avg_pow | resultado=%s W",
                    activity_id,
                    result,
                )

                return result

            # Compatibilidad/fallback para FIT que no contengan
            # est_avg_pow pero sí la serie temporal est_power.
            with fitdecode.FitReader(str(fit_path)) as fit:
                for frame in fit:
                    if not isinstance(frame, fitdecode.FitDataMessage):
                        continue

                    for field in frame.fields:
                        if field.name != "est_power":
                            continue

                        value = self._float(field.value)

                        # 0 significa ausencia de estimación en algunas
                        # muestras y no debe entrar en la media.
                        if value is not None and value > 0:
                            values.append(value)

            if not values:
                _LOGGER.warning(
                    "Coach AI Garmin: FIT %s no contiene "
                    "est_avg_pow ni valores válidos de est_power.",
                    fit_path,
                )
                return None

            average = sum(values) / len(values)
            result = round(average)

            _LOGGER.warning(
                "Coach AI Garmin: potencia estimada FIT (fallback) | "
                "activityId=%s | muestras=%s | media=%.2f W | "
                "resultado=%s W",
                activity_id,
                len(values),
                average,
                result,
            )

            return result

        except Exception:
            _LOGGER.exception(
                "Coach AI Garmin: error leyendo est_power del FIT %s.",
                fit_path,
            )
            return None

    def read_power_samples(
        self,
        activity_id: int | None,
    ) -> list[dict[str, Any]]:
        """Lee la serie temporal de potencia de una actividad Garmin.

        Prioridad:
        1. Serie ya expuesta por Home Assistant en los atributos de actividad.
        2. FIT de Garmin en /config/garmin_activities/activity_<id>.fit.

        Se devuelve una lista de diccionarios con ``timestamp``, ``power`` y
        ``power_source``. La lectura es síncrona a propósito: el coordinator
        la ejecuta mediante ``async_add_executor_job``.
        """
        if activity_id is None:
            return []

        # --------------------------------------------------------
        # 1. ATRIBUTOS DEL SENSOR GARMIN
        # --------------------------------------------------------
        for state in self.hass.states.async_all("sensor"):
            if self._activity_id(state) != int(activity_id):
                continue

            attributes = state.attributes
            for key in (
                "power_samples",
                "power_series",
                "samples",
                "activity_samples",
            ):
                raw = attributes.get(key)
                if not isinstance(raw, (list, tuple)):
                    continue

                parsed = self._parse_power_sample_collection(raw)
                if len(parsed) >= 120:
                    _LOGGER.info(
                        "Coach AI Garmin FTP: serie de potencia obtenida "
                        "desde HA | activityId=%s | muestras=%s | atributo=%s",
                        activity_id,
                        len(parsed),
                        key,
                    )
                    return parsed

            break

        # --------------------------------------------------------
        # 2. FIT GARMIN
        # --------------------------------------------------------
        fit_path = Path(
            f"/config/garmin_activities/activity_{int(activity_id)}.fit"
        )
        if not fit_path.is_file():
            _LOGGER.debug(
                "Coach AI Garmin FTP: no existe FIT para activityId=%s: %s",
                activity_id,
                fit_path,
            )
            return []

        try:
            import fitdecode
        except ImportError:
            _LOGGER.warning(
                "Coach AI Garmin FTP: fitdecode no está instalado; "
                "no se puede leer la serie temporal de potencia."
            )
            return []

        samples: list[dict[str, Any]] = []

        try:
            with fitdecode.FitReader(str(fit_path)) as fit:
                for frame in fit:
                    if not isinstance(frame, fitdecode.FitDataMessage):
                        continue

                    message_name = str(
                        getattr(frame, "name", "")
                    ).lower()
                    if message_name != "record":
                        continue

                    timestamp = None
                    power = None
                    estimated_power = None

                    for field in frame.fields:
                        name = str(
                            getattr(field, "name", "")
                        ).lower()
                        value = getattr(field, "value", None)

                        if name == "timestamp":
                            timestamp = value
                        elif name == "power":
                            power = self._float(value)
                        elif name == "est_power":
                            estimated_power = self._float(value)

                    if timestamp is None:
                        continue

                    if isinstance(timestamp, datetime):
                        timestamp_value = timestamp.timestamp()
                    else:
                        parsed_timestamp = self._parse_start_time(
                            timestamp
                        )
                        if isinstance(parsed_timestamp, datetime):
                            timestamp_value = parsed_timestamp.timestamp()
                        else:
                            try:
                                timestamp_value = float(timestamp)
                            except (TypeError, ValueError):
                                continue

                    if power is not None and power >= 0:
                        samples.append(
                            {
                                "timestamp": timestamp_value,
                                "power": power,
                                "power_source": "measured",
                            }
                        )
                    elif estimated_power is not None and estimated_power > 0:
                        samples.append(
                            {
                                "timestamp": timestamp_value,
                                "power": estimated_power,
                                "power_source": "estimated",
                            }
                        )
                    else:
                        # Conservamos el timestamp sin potencia para que el
                        # analizador detecte huecos y no los trate como 0 W.
                        samples.append(
                            {
                                "timestamp": timestamp_value,
                                "power": None,
                                "power_source": "measured",
                            }
                        )

            _LOGGER.info(
                "Coach AI Garmin FTP: serie FIT obtenida | "
                "activityId=%s | muestras=%s | archivo=%s",
                activity_id,
                len(samples),
                fit_path,
            )
            return samples

        except Exception:
            _LOGGER.exception(
                "Coach AI Garmin FTP: error leyendo serie temporal del FIT %s.",
                fit_path,
            )
            return []

    @classmethod
    def _parse_power_sample_collection(
        cls,
        raw: list[Any] | tuple[Any, ...],
    ) -> list[dict[str, Any]]:
        """Normaliza una colección de muestras expuesta como atributo HA."""
        result: list[dict[str, Any]] = []

        for item in raw:
            timestamp = None
            power = None
            source = "measured"

            if isinstance(item, dict):
                timestamp = item.get("timestamp", item.get("time"))
                power = item.get("power", item.get("watts"))
                source = str(
                    item.get(
                        "power_source",
                        item.get("source", "measured"),
                    )
                    or "measured"
                ).lower()
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                timestamp = item[0]
                power = item[1]
                if len(item) >= 3 and item[2]:
                    source = str(item[2]).lower()

            if isinstance(timestamp, datetime):
                timestamp_value = timestamp.timestamp()
            else:
                parsed = cls._parse_start_time(timestamp)
                if isinstance(parsed, datetime):
                    timestamp_value = parsed.timestamp()
                else:
                    try:
                        timestamp_value = float(timestamp)
                    except (TypeError, ValueError):
                        continue

            power_value = cls._float(power)
            if power_value is not None and power_value < 0:
                power_value = None

            if source not in {"measured", "estimated"}:
                source = "measured"

            result.append(
                {
                    "timestamp": timestamp_value,
                    "power": power_value,
                    "power_source": source,
                }
            )

        result.sort(key=lambda item: item["timestamp"])
        return result

    @staticmethod
    def _activity_start_datetime(
        state: Any,
    ) -> datetime | None:
        """Obtiene startTime de una entidad para poder ordenarla."""

        attributes = state.attributes

        value = attributes.get(
            "startTime",
            attributes.get("start_time"),
        )

        parsed = ActivityEngine._parse_start_time(value)

        if isinstance(parsed, datetime):
            return parsed

        return None

    @staticmethod
    def _activity_id(
        state: Any,
    ) -> int | None:
        """Obtiene el activityId de una entidad."""

        attributes = state.attributes

        value = attributes.get(
            "activityId",
            attributes.get("activity_id"),
        )

        return ActivityEngine._int(value)

    # ============================================================
    # BUSCAR SENSOR GARMIN
    # ============================================================

    def _find_activity_state(self) -> Any | None:
        """Busca la actividad Garmin más reciente disponible.

        No se confía ciegamente en sensor.garmin_connect_last_activity:
        si existen varias entidades Garmin con datos de actividad,
        se comparan sus startTime y se selecciona la más reciente.
        """

        candidates: list[Any] = []
        seen_entities: set[str] = set()

        # --------------------------------------------------------
        # 1. SENSOR PRINCIPAL
        # --------------------------------------------------------

        primary = self.hass.states.get(self.ENTITY_ID)

        if primary is not None:
            primary_id = self._activity_id(primary)

            if primary_id is not None:
                candidates.append(primary)
                seen_entities.add(primary.entity_id)

                _LOGGER.warning(
                    "Coach AI DEBUG Garmin: sensor principal | "
                    "entity=%s | activityId=%s | startTime=%r",
                    primary.entity_id,
                    primary_id,
                    primary.attributes.get(
                        "startTime",
                        primary.attributes.get("start_time"),
                    ),
                )
            else:
                _LOGGER.warning(
                    "Coach AI DEBUG Garmin: sensor principal existe "
                    "pero no contiene activityId. state=%s | atributos=%s.",
                    primary.state,
                    len(primary.attributes),
                )

        else:
            _LOGGER.warning(
                "Coach AI DEBUG Garmin: sensor principal %s NO EXISTE.",
                self.ENTITY_ID,
            )

        # --------------------------------------------------------
        # 2. BUSCAR TODAS LAS ENTIDADES GARMIN
        # --------------------------------------------------------

        for candidate in self.hass.states.async_all("sensor"):
            entity_id = candidate.entity_id.lower()
            attributes = candidate.attributes

            if candidate.entity_id in seen_entities:
                continue

            is_garmin = (
                "garmin" in entity_id
                or "garmin" in str(candidate.name).lower()
            )

            has_activity_id = (
                "activityId" in attributes
                or "activity_id" in attributes
            )

            has_activity_name = (
                "activityName" in attributes
                or "activity_name" in attributes
            )

            has_start_time = (
                "startTime" in attributes
                or "start_time" in attributes
            )

            if not is_garmin:
                continue

            if not (
                has_activity_id
                or (
                    has_activity_name
                    and has_start_time
                )
            ):
                continue

            candidates.append(candidate)
            seen_entities.add(candidate.entity_id)

            _LOGGER.warning(
                "Coach AI DEBUG Garmin: candidato | "
                "entity=%s | name=%s | activityId=%r | "
                "activityName=%r | startTime=%r",
                candidate.entity_id,
                candidate.name,
                attributes.get(
                    "activityId",
                    attributes.get("activity_id"),
                ),
                attributes.get(
                    "activityName",
                    attributes.get("activity_name"),
                ),
                attributes.get(
                    "startTime",
                    attributes.get("start_time"),
                ),
            )

        # --------------------------------------------------------
        # SIN CANDIDATOS
        # --------------------------------------------------------

        if not candidates:
            _LOGGER.warning(
                "Coach AI DEBUG Garmin: NO se encontró ningún "
                "sensor Garmin con atributos de actividad."
            )
            return None

        # --------------------------------------------------------
        # SELECCIONAR LA ACTIVIDAD MÁS RECIENTE
        # --------------------------------------------------------
        # Antes se seleccionaba el primer candidato que tuviera
        # activityId/startTime. Eso podía dejar bloqueado el sensor
        # principal aunque otra entidad Garmin ya tuviera una
        # actividad más reciente.
        #
        # Se ordena por:
        #   1. startTime más reciente.
        #   2. activityId mayor como desempate.
        #   3. sensor principal como último desempate.
        #
        # Las entidades sin startTime quedan al final.

        def sort_key(item: Any) -> tuple:
            start_time = self._activity_start_datetime(item)
            activity_id = self._activity_id(item) or -1
            is_primary = item.entity_id == self.ENTITY_ID

            if start_time is not None:
                try:
                    timestamp = start_time.timestamp()
                except (TypeError, ValueError, OSError):
                    timestamp = float("-inf")
            else:
                timestamp = float("-inf")

            return (
                timestamp,
                activity_id,
                1 if is_primary else 0,
            )

        candidates.sort(
            key=sort_key,
            reverse=True,
        )

        selected = candidates[0]

        _LOGGER.warning(
            "Coach AI DEBUG Garmin: SENSOR SELECCIONADO | "
            "entity=%s | name=%s | activityId=%s | startTime=%r | "
            "candidatos=%s",
            selected.entity_id,
            selected.name,
            self._activity_id(selected),
            selected.attributes.get(
                "startTime",
                selected.attributes.get("start_time"),
            ),
            len(candidates),
        )

        return selected

    # ============================================================
    # ANALIZAR ACTIVIDAD
    # ============================================================

    def analyse(
        self,
    ) -> ActivitySummary | None:
        """Analiza la actividad Garmin más reciente disponible."""

        state = self._find_activity_state()

        if state is None:
            _LOGGER.warning(
                "Coach AI DEBUG Garmin: no se ha podido localizar "
                "ningún sensor de actividad."
            )
            return None

        attributes = dict(state.attributes)

        _LOGGER.warning(
            "Coach AI DEBUG Garmin: sensor utilizado | "
            "entity=%s | state=%s | atributos=%s",
            state.entity_id,
            state.state,
            len(attributes),
        )

        _LOGGER.warning(
            "Coach AI DEBUG Garmin: atributos disponibles: %s",
            sorted(attributes.keys()),
        )

        # --------------------------------------------------------
        # ACTIVITY ID
        # --------------------------------------------------------

        activity_id = attributes.get("activityId")

        if activity_id is None:
            activity_id = attributes.get("activity_id")

        _LOGGER.warning(
            "Coach AI DEBUG Garmin: activityId bruto=%r | tipo=%s",
            activity_id,
            type(activity_id).__name__,
        )

        activity_id_int = self._int(activity_id)

        if activity_id_int is None:
            _LOGGER.warning(
                "Coach AI DEBUG Garmin: activityId inválido=%r.",
                activity_id,
            )
            return None

        # ========================================================
        # DATOS DE ACTIVIDAD
        # ========================================================

        activity_name = attributes.get("activityName")
        if activity_name is None:
            activity_name = attributes.get("activity_name")

        activity_type = attributes.get("activityType")
        if activity_type is None:
            activity_type = attributes.get("activity_type")

        distance_m = self._float(attributes.get("distance"))

        duration_seconds = self._float(
            attributes.get("duration")
        )

        elapsed_seconds = self._float(
            attributes.get("elapsedDuration")
        )
        if elapsed_seconds is None:
            elapsed_seconds = self._float(
                attributes.get("elapsed_duration")
            )

        moving_seconds = self._float(
            attributes.get("movingDuration")
        )
        if moving_seconds is None:
            moving_seconds = self._float(
                attributes.get("moving_duration")
            )

        average_speed = self._float(
            attributes.get("averageSpeed")
        )
        if average_speed is None:
            average_speed = self._float(
                attributes.get("average_speed")
            )

        max_speed = self._float(
            attributes.get("maxSpeed")
        )
        if max_speed is None:
            max_speed = self._float(
                attributes.get("max_speed")
            )

        average_hr = self._int(
            attributes.get("averageHR")
        )
        if average_hr is None:
            average_hr = self._int(
                attributes.get("avg_hr")
            )

        max_hr = self._int(
            attributes.get("maxHR")
        )
        if max_hr is None:
            max_hr = self._int(
                attributes.get("max_hr")
            )

        average_power = self._int(
            attributes.get("avgPower")
        )
        if average_power is None:
            average_power = self._int(
                attributes.get("averagePower")
            )

        # Fallback: Garmin puede no exponer avgPower en los atributos de
        # Home Assistant aunque el FIT contenga la potencia estimada de
        # Connect IQ en el Developer Field "est_power".
        power_is_estimated = False
        if average_power is None:
            average_power = self._fit_estimated_average_power(
                activity_id_int
            )
            power_is_estimated = average_power is not None

        max_power = self._int(
            attributes.get("maxPower")
        )

        normalized_power = self._int(
            attributes.get("normPower")
        )
        if normalized_power is None:
            normalized_power = self._int(
                attributes.get("normalizedPower")
            )

        calories = self._int(
            attributes.get("calories")
        )

        training_load = self._float(
            attributes.get("activityTrainingLoad")
        )
        if training_load is None:
            training_load = self._float(
                attributes.get("trainingLoad")
            )

        aerobic_training_effect = self._float(
            attributes.get("aerobicTrainingEffect")
        )

        anaerobic_training_effect = self._float(
            attributes.get("anaerobicTrainingEffect")
        )

        vo2max = self._int(
            attributes.get("vO2MaxValue")
        )
        if vo2max is None:
            vo2max = self._int(
                attributes.get("vo2max")
            )

        training_effect_label = attributes.get(
            "trainingEffectLabel"
        )

        start_time_value = attributes.get("startTime")
        if start_time_value is None:
            start_time_value = attributes.get("start_time")

        start_time = self._parse_start_time(
            start_time_value
        )

        moderate_intensity_minutes = self._int(
            attributes.get("moderateIntensityMinutes")
        )

        vigorous_intensity_minutes = self._int(
            attributes.get("vigorousIntensityMinutes")
        )

        # ========================================================
        # CONVERSIONES
        # ========================================================

        distance_km = None

        if distance_m is not None:
            distance_km = distance_m / 1000

        duration = self._duration_minutes(
            duration_seconds
        )

        elapsed_duration = self._duration_minutes(
            elapsed_seconds
        )

        moving_duration = self._duration_minutes(
            moving_seconds
        )

        # ========================================================
        # DEBUG
        # ========================================================

        _LOGGER.warning(
            "Coach AI DEBUG Garmin: datos extraídos | "
            "id=%s | nombre=%s | tipo=%s | "
            "distancia=%.3f km | duración=%s min | "
            "elapsed=%s min | moving=%s min | "
            "TSS=%s | potencia=%s | estimada=%s | FC=%s | start_time=%s",
            activity_id_int,
            activity_name,
            activity_type,
            distance_km if distance_km is not None else 0.0,
            duration,
            elapsed_duration,
            moving_duration,
            training_load,
            average_power,
            power_is_estimated,
            average_hr,
            start_time,
        )

        # ========================================================
        # CREAR ACTIVITY SUMMARY
        # ========================================================

        try:
            summary = ActivitySummary(
                activity_id=activity_id_int,
                activity_name=activity_name,
                activity_type=activity_type,
                distance_km=distance_km,
                duration=duration,
                elapsed_duration=elapsed_duration,
                moving_duration=moving_duration,
                avg_speed=average_speed,
                max_speed=max_speed,
                avg_hr=average_hr,
                max_hr=max_hr,
                avg_power=average_power,
                max_power=max_power,
                normalized_power=normalized_power,
                calories=calories,
                training_load=training_load,
                aerobic_training_effect=aerobic_training_effect,
                anaerobic_training_effect=anaerobic_training_effect,
                vo2max=vo2max,
                training_effect_label=training_effect_label,
                start_time=start_time,
                moderate_intensity_minutes=moderate_intensity_minutes,
                vigorous_intensity_minutes=vigorous_intensity_minutes,
            )

        except Exception:
            _LOGGER.exception(
                "Coach AI DEBUG Garmin: ERROR creando "
                "ActivitySummary para activityId=%s.",
                activity_id_int,
            )
            return None

        _LOGGER.warning(
            "Coach AI DEBUG Garmin: ActivitySummary creado | "
            "id=%s | nombre=%s | fecha=%s | duración=%s | "
            "TSS=%s | potencia=%s | FC=%s",
            summary.activity_id,
            summary.activity_name,
            summary.start_time,
            summary.duration,
            summary.training_load,
            summary.avg_power,
            summary.avg_hr,
        )

        return summary
