"""Calcula CTL, ATL y TSB a partir de la carga real cuando está disponible."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from .models import AthleteState


class LoadEngine:
    """Motor de carga de entrenamiento.

    Prioridad de carga diaria:
    1. TSS real de Garmin de una actividad ejecutada.
    2. TSS de ejecución guardado por Coach AI.
    3. TSS planificado como respaldo para históricos antiguos que
       todavía no tienen información de ejecución.

    Una sesión marcada explícitamente como missed/not_completed no
    aporta carga real.
    """

    CTL_DAYS = 42
    ATL_DAYS = 7
    HISTORY_DAYS = 30

    def calculate(
        self,
        athlete: AthleteState,
        history: list[dict],
    ) -> AthleteState:
        """Calcula CTL, ATL y TSB."""

        series = self.build_series(
            history,
            days=self.HISTORY_DAYS,
        )

        if series:
            latest = series[-1]
            athlete.ctl = latest["ctl"]
            athlete.atl = latest["atl"]
            athlete.tsb = latest["tsb"]
        else:
            athlete.ctl = athlete.ctl or 0
            athlete.atl = athlete.atl or 0
            athlete.tsb = athlete.ctl - athlete.atl

        return athlete

    # ============================================================
    # SERIE DE CARGA
    # ============================================================

    def build_series(
        self,
        history: list[dict],
        days: int = 30,
    ) -> list[dict]:
        """Construye la serie diaria de CTL, ATL y TSB."""

        daily_tss = self._build_daily_tss(history)

        if not daily_tss:
            return []

        first_day = min(daily_tss.keys())
        last_day = max(daily_tss.keys())

        ctl_alpha = 2 / (self.CTL_DAYS + 1)
        atl_alpha = 2 / (self.ATL_DAYS + 1)

        ctl = 0.0
        atl = 0.0
        series: list[dict] = []

        current_day = first_day

        while current_day <= last_day:
            tss = daily_tss.get(current_day, 0.0)

            ctl = ctl + ctl_alpha * (tss - ctl)
            atl = atl + atl_alpha * (tss - atl)
            tsb = ctl - atl

            series.append(
                {
                    "date": current_day.isoformat(),
                    "tss": round(tss, 1),
                    "ctl": round(ctl, 1),
                    "atl": round(atl, 1),
                    "tsb": round(tsb, 1),
                }
            )

            current_day += timedelta(days=1)

        return series[-days:]

    # ============================================================
    # TSS DIARIO
    # ============================================================

    @classmethod
    def _build_daily_tss(
        cls,
        history: list[dict],
    ) -> dict[date, float]:
        """Obtiene el TSS diario usando el estado real del día.

        Prioridad:
        1. Actividad real con TSS de Garmin/ejecución.
        2. Día marcado explícitamente como MISSED/REST/CANCELLED -> 0.
        3. Día PLANNED -> 0 (todavía no realizado).
        4. TSS planificado solo como fallback para registros antiguos
           que no contienen información de ejecución/estado.
        """

        # Por día guardamos:
        # - real: TSS de actividades realmente ejecutadas
        # - authoritative_zero: días cuyo estado confirma que no hubo carga
        # - planned: fallback de históricos antiguos
        daily: dict[date, dict[str, list[float]]] = {}

        def bucket(day: date) -> dict[str, list[float]]:
            return daily.setdefault(
                day,
                {
                    "real": [],
                    "authoritative_zero": [],
                    "planned": [],
                },
            )

        for record in history:
            record_day = cls._record_date(record)
            if record_day is None:
                continue

            execution = record.get("execution")
            if not isinstance(execution, dict):
                execution = {}

            status = str(record.get("status", "")).lower().strip()

            # ----------------------------------------------------
            # 1. CARGA REAL
            # ----------------------------------------------------
            real_tss = cls._number(execution.get("tss_real"))

            if real_tss is None:
                real_tss = cls._number(execution.get("tss"))

            if execution.get("activity_id") is not None and real_tss is not None:
                activity_day = cls._execution_date(execution) or record_day
                bucket(activity_day)["real"].append(max(0.0, real_tss))
                continue

            # También aceptamos registros completados/parciales con
            # TSS de ejecución aunque no tengan activity_id.
            if status in {"completed", "partial"} and real_tss is not None:
                bucket(record_day)["real"].append(max(0.0, real_tss))
                continue

            # ----------------------------------------------------
            # 2. ESTADOS QUE SIGNIFICAN CERO CARGA
            # ----------------------------------------------------
            # Estos estados son autoritativos: si existen para un día,
            # el target_tss planificado de otro registro del mismo día
            # NO debe convertirse en carga.
            if status in {
                "missed",
                "not_completed",
                "not completed",
                "cancelled",
                "canceled",
                "rest",
                "planned",
            }:
                bucket(record_day)["authoritative_zero"].append(0.0)
                continue

            # ----------------------------------------------------
            # 3. FALLBACK HISTÓRICO
            # ----------------------------------------------------
            # Solo registros sin estado de ejecución conocido pueden
            # aportar el TSS planificado como respaldo.
            training = record.get("training")
            if not isinstance(training, dict):
                continue

            target_tss = cls._number(training.get("target_tss"))

            if target_tss is not None:
                bucket(record_day)["planned"].append(max(0.0, target_tss))

        # --------------------------------------------------------
        # RESOLUCIÓN DIARIA
        # --------------------------------------------------------
        daily_tss: dict[date, float] = {}

        for day, values in daily.items():
            real_values = values["real"]

            if real_values:
                # Una actividad real siempre manda.
                daily_tss[day] = max(real_values)
                continue

            if values["authoritative_zero"]:
                # MISSED / REST / PLANNED / CANCELLED = 0.
                daily_tss[day] = 0.0
                continue

            if values["planned"]:
                # Histórico antiguo sin estado de ejecución.
                # Si hay varios registros del mismo día no sumamos.
                daily_tss[day] = max(values["planned"])
                continue

            daily_tss[day] = 0.0

        return daily_tss

    # ============================================================
    # FECHAS / NÚMEROS
    # ============================================================

    @staticmethod
    def _number(value: Any) -> float | None:
        """Convierte un valor a float de forma segura."""

        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _record_date(record: dict) -> date | None:
        """Obtiene la fecha del registro."""

        timestamp = record.get("timestamp")
        if not timestamp:
            return None

        return LoadEngine._parse_date(timestamp)

    @staticmethod
    def _execution_date(execution: dict) -> date | None:
        """Obtiene la fecha real de la actividad Garmin."""

        start_time = execution.get("start_time")

        if not start_time:
            return None

        return LoadEngine._parse_date(start_time)

    @staticmethod
    def _parse_date(value: Any) -> date | None:
        """Parsea timestamps ISO y fechas."""

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        try:
            timestamp_str = str(value).strip()

            if timestamp_str.endswith("Z"):
                timestamp_str = (
                    timestamp_str[:-1] + "+00:00"
                )

            return datetime.fromisoformat(
                timestamp_str
            ).date()

        except (TypeError, ValueError):
            return None
