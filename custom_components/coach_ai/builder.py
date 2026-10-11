"""Construye el estado del deportista desde Home Assistant."""

from __future__ import annotations

import logging
import re

from homeassistant.core import HomeAssistant

from .goal import GoalType
from .models import AthleteState


_LOGGER = logging.getLogger(__name__)


class AthleteBuilder:
    """Construye un AthleteState a partir de Home Assistant."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Inicializa el builder."""
        self.hass = hass
        self._garmin_cache: dict[str, str] = {}

    def _garmin_id(self, *suffixes: str) -> str:
        """Resuelve una entidad Garmin aunque cambie el prefijo/nombre.

        Primero prueba los nombres conocidos y después busca dinámicamente
        una entidad sensor que contenga el sufijo solicitado.
        """
        key = "|".join(suffixes)
        cached = self._garmin_cache.get(key)
        if cached and self.hass.states.get(cached) is not None:
            return cached

        states = self.hass.states

        # Nombres actuales/conocidos: se prioriza el prefijo del usuario.
        preferred_prefixes = (
            "sensor.fran_garmin_connect_",
            "sensor.garmin_connect_",
        )
        for suffix in suffixes:
            for prefix in preferred_prefixes:
                entity_id = f"{prefix}{suffix}"
                if states.get(entity_id) is not None:
                    self._garmin_cache[key] = entity_id
                    return entity_id

        # Fallback dinámico: busca una entidad Garmin cuyo entity_id
        # termine en el sufijo, tolerando cambios de prefijo.
        wanted = tuple(s.lower().strip() for s in suffixes if s)
        candidates: list[str] = []
        for state in states.async_all():
            entity_id = state.entity_id.lower()
            if not entity_id.startswith("sensor."):
                continue
            if "garmin" not in entity_id:
                continue
            if any(entity_id.endswith("_" + suffix) or entity_id.endswith(suffix) for suffix in wanted):
                candidates.append(state.entity_id)

        if candidates:
            candidates.sort(key=lambda x: (0 if "fran_garmin" in x.lower() else 1, x))
            entity_id = candidates[0]
            self._garmin_cache[key] = entity_id
            _LOGGER.info(
                "Coach AI Garmin Resolver: %s → %s",
                key,
                entity_id,
            )
            return entity_id

        # Devuelve el nombre estándar para que _state/_numeric_value
        # simplemente obtengan None si Garmin no lo ofrece.
        return f"sensor.garmin_connect_{suffixes[0]}"

    # ============================================================
    # UTILIDADES
    # ============================================================

    def _get_entity(self, entity_id: str):
        """Obtiene una entidad de Home Assistant."""
        return self.hass.states.get(entity_id)

    def _state(self, entity_id: str):
        """Obtiene el valor de una entidad."""

        state = self._get_entity(entity_id)

        if state is None:
            return None

        raw_state = state.state

        if raw_state not in (
            "unknown",
            "unavailable",
            "",
            None,
        ):
            return raw_state

        attributes = state.attributes

        possible_keys = (
            "value",
            "state",
            "value_numeric",
            "numeric_value",
            "measurement",
            "duration",
            "minutes",
        )

        for key in possible_keys:
            value = attributes.get(key)

            if value not in (
                None,
                "",
                "unknown",
                "unavailable",
            ):
                return value

        return None

    def _numeric_value(
        self,
        entity_id: str,
    ) -> float | None:
        """Extrae un número de una entidad."""

        value = self._state(entity_id)

        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        text = str(value).strip()

        try:
            return float(text)
        except ValueError:
            pass

        match = re.search(
            r"(-?\d+(?:[.,]\d+)?)",
            text,
        )

        if match:
            try:
                return float(
                    match.group(1).replace(",", ".")
                )
            except ValueError:
                return None

        return None

    def _int(
        self,
        entity_id: str,
    ) -> int | None:
        """Convierte una entidad a entero."""

        value = self._numeric_value(entity_id)

        if value is None:
            return None

        try:
            return int(round(value))
        except (TypeError, ValueError):
            return None

    def _float(
        self,
        entity_id: str,
    ) -> float | None:
        """Convierte una entidad a float."""
        return self._numeric_value(entity_id)

    def _string(
        self,
        entity_id: str,
    ) -> str | None:
        """Devuelve una cadena."""

        value = self._state(entity_id)

        if value is None:
            return None

        return str(value)

    # ============================================================
    # POTENCIA / FTP
    # ============================================================

    def _get_ftp(
        self,
        weight: float | None,
    ) -> float | None:
        """Obtiene FTP de Garmin o lo estima mediante W/kg."""

        # FTP directo.
        # Entidad confirmada en la instalación del usuario.
        ftp_entity = "sensor.fran_garmin_connect_ftp_cycling"
        ftp = self._float(ftp_entity)

        _LOGGER.debug(
            "Coach AI Power: FTP entity=%s | state=%s | value=%s",
            ftp_entity,
            self._state(ftp_entity),
            ftp,
        )

        if ftp is not None and ftp > 0:
            _LOGGER.info(
                "Coach AI Power: FTP Garmin = %.1f W",
                ftp,
            )
            return round(ftp, 1)

        # Fallback mediante W/kg
        power_to_weight = self._float(
            self._garmin_id("power_to_weight_cycling")
        )

        if (
            power_to_weight is not None
            and power_to_weight > 0
            and weight is not None
            and weight > 0
        ):
            estimated_ftp = round(
                power_to_weight * weight,
                1,
            )

            _LOGGER.warning(
                "Coach AI Power: FTP estimado = "
                "%.3f W/kg × %.1f kg = %.1f W",
                power_to_weight,
                weight,
                estimated_ftp,
            )

            return estimated_ftp

        _LOGGER.debug(
            "Coach AI Power: no se ha podido obtener FTP "
            "| entidad=%s | state=%s",
            ftp_entity,
            self._state(ftp_entity),
        )

        return None

    # ============================================================
    # SUEÑO
    # ============================================================

    def _sleep_minutes(
        self,
        entity_id: str,
    ) -> float | None:
        """Obtiene un valor de sueño expresado en minutos."""

        value = self._float(entity_id)

        if value is None or value <= 0:
            return None

        # Algunos sensores Garmin proporcionan segundos.
        if value > 1000:
            return value / 60.0

        return value

    def _sleep_quality(
        self,
        score: int | None,
    ) -> str | None:
        """Clasifica la calidad del sueño."""

        if score is None:
            return None

        if score >= 90:
            return "Excelente"

        if score >= 75:
            return "Buena"

        if score >= 60:
            return "Regular"

        if score >= 40:
            return "Baja"

        return "Muy baja"

    def _calculate_sleep_score(
        self,
    ) -> tuple[
        int | None,
        float | None,
        float | None,
        float | None,
        float | None,
        float | None,
    ]:
        """Calcula el Sleep Score de Coach AI."""

        sleep_duration = self._sleep_minutes(
            self._garmin_id("sleep_duration")
        )

        total_sleep_duration = self._sleep_minutes(
            self._garmin_id("total_sleep_duration")
        )

        deep_sleep = self._sleep_minutes(
            self._garmin_id("deep_sleep")
        )

        rem_sleep = self._sleep_minutes(
            self._garmin_id("rem_sleep")
        )

        awake_duration = self._sleep_minutes(
            self._garmin_id("awake_duration")
        )

        unmeasurable_sleep = self._sleep_minutes(
            self._garmin_id("unmeasurable_sleep")
        )

        _LOGGER.info(
            "Coach AI Sleep READ: "
            "sleep=%s total=%s deep=%s rem=%s "
            "awake=%s unmeasurable=%s",
            sleep_duration,
            total_sleep_duration,
            deep_sleep,
            rem_sleep,
            awake_duration,
            unmeasurable_sleep,
        )

        duration = sleep_duration

        if duration is None:
            duration = total_sleep_duration

        # Algunos sensores proporcionan awake en segundos.
        if (
            awake_duration is not None
            and duration is not None
            and awake_duration > duration
        ):
            converted_awake = (
                awake_duration / 60.0
            )

            if converted_awake <= duration:
                awake_duration = converted_awake
            else:
                _LOGGER.warning(
                    "Coach AI Sleep: awake_duration=%s "
                    "descartado por valor anómalo.",
                    awake_duration,
                )
                awake_duration = None

        # Sin datos detallados: utilizar Garmin Sleep Score.
        if (
            duration is None
            and deep_sleep is None
            and rem_sleep is None
            and awake_duration is None
        ):
            garmin_score = self._int(
                self._garmin_id("sleep_score")
            )

            return (
                garmin_score,
                duration,
                deep_sleep,
                rem_sleep,
                awake_duration,
                unmeasurable_sleep,
            )

        components: list[tuple[float, float]] = []

        # --------------------------------------------------------
        # Duración - 45 %
        # --------------------------------------------------------

        if duration is not None:

            hours = duration / 60.0

            if 7.5 <= hours <= 9.0:
                duration_score = 100.0

            elif hours < 7.5:
                duration_score = max(
                    0.0,
                    100.0
                    - (
                        (7.5 - hours)
                        * 20.0
                    ),
                )

            else:
                duration_score = max(
                    80.0,
                    100.0
                    - (
                        (hours - 9.0)
                        * 10.0
                    ),
                )

            components.append(
                (
                    duration_score,
                    0.45,
                )
            )

        # --------------------------------------------------------
        # Profundo - 20 %
        # --------------------------------------------------------

        if (
            deep_sleep is not None
            and duration is not None
            and duration > 0
        ):

            deep_ratio = (
                deep_sleep / duration
            )

            if 0.15 <= deep_ratio <= 0.25:
                deep_score = 100.0

            elif deep_ratio < 0.15:
                deep_score = max(
                    0.0,
                    100.0
                    - (
                        (0.15 - deep_ratio)
                        * 400.0
                    ),
                )

            else:
                deep_score = max(
                    85.0,
                    100.0
                    - (
                        (deep_ratio - 0.25)
                        * 300.0
                    ),
                )

            components.append(
                (
                    deep_score,
                    0.20,
                )
            )

        # --------------------------------------------------------
        # REM - 20 %
        # --------------------------------------------------------

        if (
            rem_sleep is not None
            and duration is not None
            and duration > 0
        ):

            rem_ratio = (
                rem_sleep / duration
            )

            if 0.20 <= rem_ratio <= 0.30:
                rem_score = 100.0

            elif rem_ratio < 0.20:
                rem_score = max(
                    0.0,
                    100.0
                    - (
                        (0.20 - rem_ratio)
                        * 400.0
                    ),
                )

            else:
                rem_score = max(
                    85.0,
                    100.0
                    - (
                        (rem_ratio - 0.30)
                        * 300.0
                    ),
                )

            components.append(
                (
                    rem_score,
                    0.20,
                )
            )

        # --------------------------------------------------------
        # Continuidad - 15 %
        # --------------------------------------------------------

        if (
            awake_duration is not None
            and duration is not None
            and duration > 0
        ):

            awake_ratio = (
                awake_duration / duration
            )

            if awake_ratio <= 0.05:
                awake_score = 100.0

            elif awake_ratio <= 0.10:
                awake_score = 90.0

            elif awake_ratio <= 0.15:
                awake_score = 75.0

            elif awake_ratio <= 0.20:
                awake_score = 60.0

            else:
                awake_score = max(
                    20.0,
                    60.0
                    - (
                        (awake_ratio - 0.20)
                        * 200.0
                    ),
                )

            components.append(
                (
                    awake_score,
                    0.15,
                )
            )

        # --------------------------------------------------------
        # Sin componentes
        # --------------------------------------------------------

        if not components:

            garmin_score = self._int(
                self._garmin_id("sleep_score")
            )

            return (
                garmin_score,
                duration,
                deep_sleep,
                rem_sleep,
                awake_duration,
                unmeasurable_sleep,
            )

        # --------------------------------------------------------
        # Score ponderado
        # --------------------------------------------------------

        total_weight = sum(
            weight
            for _, weight in components
        )

        weighted_score = sum(
            value * weight
            for value, weight in components
        )

        score = (
            weighted_score / total_weight
        )

        # --------------------------------------------------------
        # Sueño no medible
        # --------------------------------------------------------

        if (
            unmeasurable_sleep is not None
            and duration is not None
            and duration > 0
        ):

            unmeasurable_ratio = (
                unmeasurable_sleep
                / duration
            )

            if unmeasurable_ratio > 0.10:
                score -= 5.0

            elif unmeasurable_ratio > 0.05:
                score -= 2.0

        score = max(
            0.0,
            min(
                100.0,
                score,
            ),
        )

        score_int = int(
            round(score)
        )

        _LOGGER.info(
            "Coach AI Sleep SCORE=%s | "
            "duration=%s | deep=%s | rem=%s | awake=%s",
            score_int,
            duration,
            deep_sleep,
            rem_sleep,
            awake_duration,
        )

        return (
            score_int,
            duration,
            deep_sleep,
            rem_sleep,
            awake_duration,
            unmeasurable_sleep,
        )

    # ============================================================
    # HRV
    # ============================================================

    def _get_hrv_status(self) -> str | None:
        """Obtiene el estado HRV de Garmin."""

        status: str | None = None

        # --------------------------------------------------------
        # Estado HRV directo
        # --------------------------------------------------------

        hrv_status = self._string(
            self._garmin_id("hrv_status")
        )

        if hrv_status is not None:

            normalized = (
                hrv_status.strip().lower()
            )

            if normalized not in (
                "unknown",
                "unavailable",
                "",
            ):
                return hrv_status

        # --------------------------------------------------------
        # HRV numérico de última noche
        # --------------------------------------------------------

        hrv_last_night = self._float(
            self._garmin_id("hrv_last_night_average")
        )

        hrv_baseline = self._float(
            self._garmin_id("hrv_baseline")
        )

        hrv_weekly = self._float(
            self._garmin_id("hrv_weekly_average")
        )

        if (
            hrv_last_night is not None
            and hrv_last_night > 0
        ):

            reference = hrv_baseline

            if (
                reference is None
                or reference <= 0
            ):
                reference = hrv_weekly

            if (
                reference is not None
                and reference > 0
            ):

                variation = (
                    (
                        hrv_last_night
                        - reference
                    )
                    / reference
                ) * 100.0

                if variation >= 10:
                    status = "Favorable"

                elif variation >= -5:
                    status = "Normal"

                elif variation >= -15:
                    status = "Reducido"

                else:
                    status = "Bajo"

                _LOGGER.info(
                    "Coach AI HRV: %.1f ms | "
                    "referencia %.1f ms | "
                    "variación %.1f%% | estado=%s",
                    hrv_last_night,
                    reference,
                    variation,
                    status,
                )

                return status

            _LOGGER.info(
                "Coach AI HRV: %.1f ms disponible "
                "pero sin baseline.",
                hrv_last_night,
            )

            return "Disponible"

        # --------------------------------------------------------
        # HRV no disponible
        # --------------------------------------------------------

        resting_hr = self._float(
            self._garmin_id("resting_heart_rate")
        )

        resting_hr_7d = self._float(
            self._garmin_id("7_day_average_resting_heart_rate")
        )

        if (
            resting_hr is not None
            and resting_hr_7d is not None
            and resting_hr_7d > 0
        ):

            difference = (
                resting_hr
                - resting_hr_7d
            )

            if difference <= -3:
                alternative = "RHR favorable"

            elif difference <= 2:
                alternative = "RHR estable"

            elif difference <= 5:
                alternative = "RHR elevada"

            else:
                alternative = "RHR muy elevada"

            _LOGGER.info(
                "Coach AI HRV: no disponible. "
                "Señal RHR: actual=%s | "
                "media7d=%s | diferencia=%s | %s",
                resting_hr,
                resting_hr_7d,
                round(difference, 1),
                alternative,
            )

        return "No disponible"

    # ============================================================
    # METEOROLOGÍA
    # ============================================================

    def _get_temperature(self) -> float | None:
        """Obtiene temperatura exterior."""

        entities = (
            "sensor.aemet_temperature",
            "sensor.aemet_temperatura",
            "sensor.openweathermap_temperature",
        )

        for entity_id in entities:
            value = self._float(entity_id)

            if value is not None:
                return value

        return None

    def _get_humidity(self) -> float | None:
        """Obtiene humedad exterior."""

        entities = (
            "sensor.aemet_humidity",
            "sensor.aemet_humedad",
        )

        for entity_id in entities:
            value = self._float(entity_id)

            if value is not None:
                return value

        return None

    def _get_wind_speed(self) -> float | None:
        """Obtiene velocidad del viento."""

        entities = (
            "sensor.aemet_wind_speed",
            "sensor.aemet_viento",
        )

        for entity_id in entities:
            value = self._float(entity_id)

            if value is not None:
                return value

        return None

    def _get_raining(self) -> bool:
        """Determina si está lloviendo."""

        entities = (
            "binary_sensor.aemet_rain",
            "binary_sensor.aemet_lluvia",
        )

        for entity_id in entities:
            state = self._state(entity_id)

            if state is None:
                continue

            normalized = (
                str(state)
                .strip()
                .lower()
            )

            if normalized in (
                "on",
                "true",
                "yes",
                "rain",
                "lluvia",
            ):
                return True

            if normalized in (
                "off",
                "false",
                "no",
                "clear",
                "none",
            ):
                return False

        return False

    # ============================================================
    # OBJETIVO
    # ============================================================

    def _get_goal(self) -> GoalType:
        """Obtiene el objetivo configurado."""

        goal = GoalType.MAINTENANCE

        goal_state = self._string(
            "input_select.coach_ai_goal"
        )

        if not goal_state:
            return goal

        normalized = (
            goal_state
            .strip()
            .lower()
        )

        goal_mapping = {
            "ftp": GoalType.FTP,
            "pérdida de peso": GoalType.WEIGHT_LOSS,
            "perdida de peso": GoalType.WEIGHT_LOSS,
            "weight loss": GoalType.WEIGHT_LOSS,
            "resistencia": GoalType.ENDURANCE,
            "endurance": GoalType.ENDURANCE,
            "mantenimiento": GoalType.MAINTENANCE,
            "maintenance": GoalType.MAINTENANCE,
        }

        return goal_mapping.get(
            normalized,
            goal,
        )

    # ============================================================
    # DISPONIBILIDAD
    # ============================================================

    def _get_available_minutes(self) -> int:
        """Obtiene los minutos disponibles para entrenar."""

        available = self._int(
            "input_number.coach_ai_available_minutes"
        )

        if available is None:
            return 60

        return max(
            0,
            available,
        )

    # ============================================================
    # BUILD
    # ============================================================

    def build(self) -> AthleteState:
        """Construye el estado completo del deportista."""

        # --------------------------------------------------------
        # Garmin
        # --------------------------------------------------------

        body_battery = self._int(
            self._garmin_id("body_battery")
        )

        training_readiness = self._int(
            self._garmin_id("training_readiness")
        )

        stress = self._int(
            self._garmin_id("average_stress_level")
        )

        resting_hr = self._int(
            self._garmin_id("resting_heart_rate")
        )

        max_hr = self._int(
            self._garmin_id("maximum_heart_rate")
        )

        vo2max = self._int(
            self._garmin_id("vo2_max")
        )

        # --------------------------------------------------------
        # Peso
        # --------------------------------------------------------

        weight = self._float(
            "sensor.tito_weight"
        )

        # --------------------------------------------------------
        # FTP
        # --------------------------------------------------------

        ftp = self._get_ftp(
            weight
        )

        # --------------------------------------------------------
        # Sueño
        # --------------------------------------------------------

        (
            sleep_score,
            sleep_duration,
            deep_sleep,
            rem_sleep,
            awake_duration,
            unmeasurable_sleep,
        ) = self._calculate_sleep_score()

        sleep_quality = self._sleep_quality(
            sleep_score
        )

        sleep_score_method = None

        if sleep_score is not None:
            sleep_score_method = "Coach AI"

        # --------------------------------------------------------
        # HRV
        # --------------------------------------------------------

        hrv_status = self._get_hrv_status()

        # --------------------------------------------------------
        # Meteorología
        # --------------------------------------------------------

        temperature = self._get_temperature()

        humidity = self._get_humidity()

        wind_speed = self._get_wind_speed()

        raining = self._get_raining()

        # --------------------------------------------------------
        # Disponibilidad
        # --------------------------------------------------------

        available_minutes = (
            self._get_available_minutes()
        )

        # --------------------------------------------------------
        # Objetivo
        # --------------------------------------------------------

        goal = self._get_goal()

        # --------------------------------------------------------
        # AthleteState
        # --------------------------------------------------------

        athlete = AthleteState(
            body_battery=body_battery,
            sleep_score=sleep_score,
            sleep_duration=sleep_duration,
            deep_sleep=deep_sleep,
            rem_sleep=rem_sleep,
            awake_duration=awake_duration,
            unmeasurable_sleep=unmeasurable_sleep,
            sleep_score_method=sleep_score_method,
            sleep_quality=sleep_quality,
            training_readiness=training_readiness,
            hrv_status=hrv_status,
            stress=stress,
            resting_hr=resting_hr,
            max_hr=max_hr,
            vo2max=vo2max,
            ftp=ftp,
            weight=weight,
            age=None,
            ctl=None,
            atl=None,
            tsb=None,
            weekly_tss=None,
            monthly_tss=None,
            temperature=temperature,
            humidity=humidity,
            wind_speed=wind_speed,
            raining=raining,
            available_minutes=available_minutes,
            next_race=None,
            days_to_race=None,
            goal=goal,
        )

        _LOGGER.info(
            "Coach AI AthleteBuilder: "
            "BodyBattery=%s | Sleep=%s | HRV=%s | "
            "RHR=%s | VO2max=%s | Weight=%s | FTP=%s | "
            "Temperature=%s | Goal=%s",
            body_battery,
            sleep_score,
            hrv_status,
            resting_hr,
            vo2max,
            weight,
            ftp,
            temperature,
            goal,
        )

        return athlete