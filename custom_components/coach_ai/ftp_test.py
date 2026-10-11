"""Motor de test y análisis FTP de Coach AI.

Genera un test FTP estructurado de 60 minutos y analiza la actividad real
de Garmin usando la serie temporal de potencia cuando está disponible.

Importante:
- El bloque de 20 minutos es OPEN: no fija una potencia objetivo.
- El FTP actual NO se modifica desde este módulo.
- La estimación clásica es potencia media de 20 min × 0,95.
- La recomendación es informativa; no escribe el FTP de Garmin.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from statistics import fmean, pstdev
from typing import Any, Iterable

from .models import Interval, TrainingPlan


FTP_TEST_NAME = "FTP Test - 20 min v3"
FTP_TEST_DURATION = 60
FTP_TEST_BLOCK_DURATION = 20
FTP_TEST_EXPECTED_START = 32 * 60
FTP_20_MIN_FACTOR = 0.95
FTP_WINDOW_SECONDS = FTP_TEST_BLOCK_DURATION * 60


@dataclass(slots=True, frozen=True)
class FTPTestResult:
    """Resultado del análisis de un test FTP."""

    power_20min: float | None
    ftp_95: float | None
    ftp_previous: float | None = None
    ftp_intervals: float | None = None
    ftp_recommended: float | None = None
    confidence: float | None = None
    status: str = "pending"
    message: str = ""

    # Metadatos del análisis automático. Todos son opcionales para mantener
    # compatibilidad con llamadas antiguas a FTPTestResult.
    activity_id: int | None = None
    window_start_seconds: float | None = None
    window_end_seconds: float | None = None
    coverage_percent: float | None = None
    power_source: str | None = None
    power_std_percent: float | None = None
    split_difference_percent: float | None = None
    intervals_entity: str | None = None


class FTPTestEngine:
    """Genera y analiza el test FTP de Coach AI."""

    # ------------------------------------------------------------
    # GENERACIÓN
    # ------------------------------------------------------------

    def generate(
        self,
        previous_ftp: float | None = None,
    ) -> TrainingPlan:
        """Genera un test FTP completo de 60 minutos.

        El bloque de 20 minutos es OPEN para que el ciclista
        realice un esfuerzo máximo sostenible sin que Garmin
        imponga una potencia basada en el FTP anterior.
        """

        previous_ftp = self._safe_positive(previous_ftp)

        # Potencias de preparación calculadas sobre el FTP actual.
        # El bloque de 20 min permanece OPEN deliberadamente: no debe
        # imponer una potencia objetivo durante la medición del FTP.
        def target_power(factor: float) -> int | None:
            if previous_ftp is None:
                return None
            return max(1, round(previous_ftp * factor))

        # Interval.duration usa SEGUNDOS porque este valor termina directamente en Garmin.
        # El TrainingPlan.duration general continúa expresado en minutos.
        intervals = [
            Interval(
                name="Calentamiento",
                duration=12 * 60,
                power=target_power(0.55),
                heart_rate=None,
                cadence=90,
                step_type="warmup",
                intensity="active",
            ),
            Interval(
                name="Activación",
                duration=3 * 60,
                power=target_power(0.75),
                heart_rate=None,
                cadence=100,
                step_type="interval",
                intensity="active",
            ),
            Interval(
                name="Recuperación",
                duration=4 * 60,
                power=target_power(0.50),
                heart_rate=None,
                cadence=85,
                step_type="recovery",
                intensity="rest",
            ),
            Interval(
                name="Blow-out",
                duration=5 * 60,
                power=target_power(1.05),
                heart_rate=None,
                cadence=100,
                step_type="interval",
                intensity="active",
            ),
            Interval(
                name="Recuperación antes del test",
                duration=8 * 60,
                power=target_power(0.50),
                heart_rate=None,
                cadence=85,
                step_type="recovery",
                intensity="rest",
            ),
            Interval(
                name="TEST FTP 20 MIN - OPEN",
                duration=20 * 60,
                power=None,
                heart_rate=None,
                cadence=None,
                step_type="interval",
                intensity="active",
            ),
            Interval(
                name="Vuelta a la calma",
                duration=8 * 60,
                power=target_power(0.45),
                heart_rate=None,
                cadence=85,
                step_type="cooldown",
                intensity="rest",
            ),
        ]

        metadata: dict[str, Any] = {
            "test_type": "ftp_20min",
            "test_version": 2,
            "test_duration_minutes": FTP_TEST_DURATION,
            "test_block_minutes": FTP_TEST_BLOCK_DURATION,
            "test_block_expected_start_seconds": FTP_TEST_EXPECTED_START,
            "ftp_formula": "20min_power_x_0.95",
            "previous_ftp": previous_ftp,
            "open_test_block": True,
        }

        return TrainingPlan(
            workout=FTP_TEST_NAME,
            duration=FTP_TEST_DURATION,
            zone="FTP_TEST",
            target_power=None,
            target_hr=None,
            cadence=None,
            target_tss=None,
            intensity_factor=None,
            outdoor=False,
            reason=(
                "Test FTP de 20 minutos. "
                "El bloque de test es OPEN: busca la mayor potencia "
                "media sostenible durante 20 minutos sin salir "
                "demasiado fuerte al inicio."
            ),
            intervals=intervals,
            export=metadata,
        )

    # ------------------------------------------------------------
    # ANÁLISIS CLÁSICO
    # ------------------------------------------------------------

    def analyse_power(
        self,
        power_20min: float | int | None,
        *,
        previous_ftp: float | int | None = None,
        intervals_ftp: float | int | None = None,
    ) -> FTPTestResult:
        """Calcula el FTP clásico y conserva la comparación futura."""

        power = self._safe_positive(power_20min)
        previous = self._safe_positive(previous_ftp)
        intervals = self._safe_positive(intervals_ftp)

        if power is None:
            return FTPTestResult(
                power_20min=None,
                ftp_95=None,
                ftp_previous=previous,
                ftp_intervals=intervals,
                status="invalid",
                message=(
                    "No hay potencia media válida del bloque "
                    "de 20 minutos."
                ),
            )

        ftp_95 = round(power * FTP_20_MIN_FACTOR, 1)

        return FTPTestResult(
            power_20min=round(power, 1),
            ftp_95=ftp_95,
            ftp_previous=previous,
            ftp_intervals=intervals,
            status="valid",
            message=(
                "Test válido. FTP estimado mediante potencia media "
                "de 20 minutos × 0,95."
            ),
        )

    # ------------------------------------------------------------
    # ANÁLISIS AUTOMÁTICO DE SERIE
    # ------------------------------------------------------------

    def analyse_power_series(
        self,
        samples: Iterable[Any],
        *,
        previous_ftp: float | int | None = None,
        intervals_ftp: float | int | None = None,
        intervals_entity: str | None = None,
        activity_id: int | None = None,
        expected_start_seconds: float = FTP_TEST_EXPECTED_START,
    ) -> FTPTestResult:
        """Encuentra el mejor bloque continuo de 20 min y calcula el FTP.

        ``samples`` acepta diccionarios con ``timestamp``/``power`` o
        tuplas de 2-3 elementos ``(timestamp, power[, source])``.
        Los timestamps deben ser segundos absolutos o relativos; para la
        búsqueda del mejor bloque solo importa su orden temporal.
        """

        previous = self._safe_positive(previous_ftp)
        intervals = self._safe_positive(intervals_ftp)
        normalized = self._normalize_samples(samples)

        if len(normalized) < 120:
            return FTPTestResult(
                power_20min=None,
                ftp_95=None,
                ftp_previous=previous,
                ftp_intervals=intervals,
                status="invalid",
                confidence=0.0,
                activity_id=activity_id,
                intervals_entity=intervals_entity,
                message=(
                    "No hay suficientes muestras de potencia para "
                    "analizar el test FTP."
                ),
            )

        seconds = self._resample_to_seconds(normalized)
        candidate = self._find_best_window(
            seconds,
            expected_start_seconds=expected_start_seconds,
        )

        if candidate is None:
            return FTPTestResult(
                power_20min=None,
                ftp_95=None,
                ftp_previous=previous,
                ftp_intervals=intervals,
                status="invalid",
                confidence=0.0,
                activity_id=activity_id,
                intervals_entity=intervals_entity,
                message=(
                    "No se ha encontrado un bloque continuo de 20 minutos "
                    "con potencia suficiente para validar el test."
                ),
            )

        start_idx, end_idx, avg_power, coverage = candidate
        values = [
            power
            for _, power, _ in seconds[start_idx:end_idx]
            if power is not None
        ]

        if not values or avg_power is None:
            return FTPTestResult(
                power_20min=None,
                ftp_95=None,
                ftp_previous=previous,
                ftp_intervals=intervals,
                status="invalid",
                confidence=0.0,
                activity_id=activity_id,
                intervals_entity=intervals_entity,
                message="El bloque candidato no contiene potencia válida.",
            )

        ftp_95 = round(avg_power * FTP_20_MIN_FACTOR, 1)
        power_source = self._dominant_power_source(
            seconds[start_idx:end_idx]
        )

        first_5 = self._window_average(values[: min(300, len(values))])
        last_5 = self._window_average(values[-min(300, len(values)):])
        split_difference = None
        if first_5 and last_5:
            split_difference = round(
                abs(last_5 - first_5)
                / ((last_5 + first_5) / 2)
                * 100,
                1,
            )

        std_percent = None
        if avg_power and len(values) >= 30:
            std_percent = round(
                pstdev(values) / avg_power * 100,
                1,
            )

        status = "valid"
        if coverage < 0.95:
            status = "partial" if coverage >= 0.90 else "invalid"
        if power_source == "estimated" and status == "valid":
            status = "partial"

        # Un bloque FTP real puede tener pacing, pero una diferencia enorme
        # entre los primeros y últimos 5 minutos suele indicar que no se ha
        # completado el esfuerzo de 20 min de forma válida.
        if split_difference is not None:
            if split_difference > 35.0:
                status = "invalid"
            elif split_difference > 20.0 and status == "valid":
                status = "partial"

        if std_percent is not None:
            if std_percent > 40.0:
                status = "invalid"
            elif std_percent > 25.0 and status == "valid":
                status = "partial"

        confidence = self._confidence(
            coverage=coverage,
            power_source=power_source,
            split_difference=split_difference,
            values=values,
        )

        ftp_recommended = (
            self._recommend_ftp(ftp_95, intervals)
            if status == "valid"
            else None
        )

        message = self._build_message(
            status=status,
            power=avg_power,
            ftp_95=ftp_95,
            ftp_recommended=ftp_recommended,
            coverage=coverage,
            power_source=power_source,
            split_difference=split_difference,
            intervals_ftp=intervals,
        )

        return FTPTestResult(
            power_20min=round(avg_power, 1),
            ftp_95=ftp_95,
            ftp_previous=previous,
            ftp_intervals=intervals,
            ftp_recommended=ftp_recommended,
            confidence=round(confidence, 1),
            status=status,
            message=message,
            activity_id=activity_id,
            window_start_seconds=seconds[start_idx][0],
            window_end_seconds=seconds[end_idx - 1][0] + 1,
            coverage_percent=round(coverage * 100, 1),
            power_source=power_source,
            power_std_percent=std_percent,
            split_difference_percent=split_difference,
            intervals_entity=intervals_entity,
        )

    # ------------------------------------------------------------
    # SERIE / VENTANA
    # ------------------------------------------------------------

    @classmethod
    def _normalize_samples(
        cls,
        samples: Iterable[Any],
    ) -> list[tuple[float, float | None, str]]:
        """Normaliza muestras de Garmin a timestamp/potencia/origen."""

        normalized: list[tuple[float, float | None, str]] = []

        for sample in samples:
            timestamp: Any = None
            power: Any = None
            source = "measured"

            if isinstance(sample, dict):
                timestamp = sample.get("timestamp")
                power = sample.get("power")
                source = str(
                    sample.get("power_source", sample.get("source", "measured"))
                    or "measured"
                ).lower()
            elif isinstance(sample, (list, tuple)) and len(sample) >= 2:
                timestamp = sample[0]
                power = sample[1]
                if len(sample) >= 3 and sample[2]:
                    source = str(sample[2]).lower()

            try:
                ts = float(timestamp)
            except (TypeError, ValueError):
                continue

            if not isfinite(ts):
                continue

            value = cls._safe_positive(power, allow_zero=True)
            if source not in {"estimated", "measured"}:
                source = "measured"

            normalized.append((ts, value, source))

        normalized.sort(key=lambda item: item[0])

        deduped: list[tuple[float, float | None, str]] = []
        for item in normalized:
            if deduped and abs(deduped[-1][0] - item[0]) < 0.001:
                # Priorizar una muestra medida sobre una estimada.
                if deduped[-1][2] == "estimated" and item[2] == "measured":
                    deduped[-1] = item
                elif deduped[-1][1] is None and item[1] is not None:
                    deduped[-1] = item
                continue
            deduped.append(item)

        return deduped

    @classmethod
    def _resample_to_seconds(
        cls,
        samples: list[tuple[float, float | None, str]],
    ) -> list[tuple[int, float | None, str]]:
        """Interpola una serie irregular a 1 Hz usando tiempo relativo."""

        if not samples:
            return []

        base = samples[0][0]
        relative = [
            (ts - base, power, source)
            for ts, power, source in samples
        ]

        start = 0
        end = int(round(relative[-1][0]))
        if end <= start:
            return []

        result: list[tuple[int, float | None, str]] = []
        cursor = 0

        for second in range(start, end + 1):
            while (
                cursor + 1 < len(relative)
                and relative[cursor + 1][0] < second
            ):
                cursor += 1

            left = relative[cursor]
            right = relative[min(cursor + 1, len(relative) - 1)]

            value: float | None = None
            source = left[2]

            if abs(left[0] - second) <= 0.51:
                value = left[1]
                source = left[2]
            elif (
                right[0] != left[0]
                and left[1] is not None
                and right[1] is not None
            ):
                gap = right[0] - left[0]
                if gap <= 5.0 and left[0] <= second <= right[0]:
                    ratio = (second - left[0]) / gap
                    value = left[1] + (right[1] - left[1]) * ratio
                    source = (
                        "estimated"
                        if "estimated" in {left[2], right[2]}
                        else "measured"
                    )

            result.append((second, value, source))

        return result

    @classmethod
    def _find_best_window(
        cls,
        seconds: list[tuple[int, float | None, str]],
        *,
        expected_start_seconds: float,
    ) -> tuple[int, int, float, float] | None:
        """Busca el máximo de potencia media en 20 min con cobertura >=90 %."""

        window = FTP_WINDOW_SECONDS
        if len(seconds) < window:
            return None

        values = [power for _, power, _ in seconds]
        prefix_sum = [0.0]
        prefix_count = [0]
        for value in values:
            prefix_sum.append(prefix_sum[-1] + (value or 0.0))
            prefix_count.append(prefix_count[-1] + (1 if value is not None else 0))

        candidates: list[tuple[float, int, int, float]] = []

        all_starts = range(0, len(seconds) - window + 1)
        expected_min = max(0, int(expected_start_seconds) - 600)
        expected_max = int(expected_start_seconds) + 600
        constrained_starts = [
            start
            for start in all_starts
            if expected_min <= seconds[start][0] <= expected_max
        ]

        # El test programado empieza a los 32:00. Primero buscamos alrededor
        # de esa posición; si la grabación no encaja, hacemos fallback global.
        starts = constrained_starts or list(all_starts)

        for start in starts:
            end = start + window
            count = prefix_count[end] - prefix_count[start]
            coverage = count / window
            if coverage < 0.90 or count < 1080:
                continue

            total = prefix_sum[end] - prefix_sum[start]
            average = total / count

            candidates.append((
                average,
                start,
                end,
                coverage,
            ))

        if not candidates:
            return None

        # La potencia manda; a igualdad razonable favorecemos la posición
        # esperada de 32:00 para evitar elegir por azar otra ventana.
        candidates.sort(
            key=lambda item: (
                item[0],
                -abs(seconds[item[1]][0] - expected_start_seconds),
            ),
            reverse=True,
        )

        average, start, end, coverage = candidates[0]
        return start, end, average, coverage

    # ------------------------------------------------------------
    # CALIDAD / RECOMENDACIÓN
    # ------------------------------------------------------------

    @staticmethod
    def _confidence(
        *,
        coverage: float,
        power_source: str,
        split_difference: float | None,
        values: list[float],
    ) -> float:
        """Calcula confianza 0-100 de forma conservadora."""

        score = min(55.0, coverage * 55.0)

        if power_source == "measured":
            score += 15.0
        else:
            score += 7.0

        if split_difference is None:
            score += 10.0
        elif split_difference <= 5.0:
            score += 20.0
        elif split_difference <= 10.0:
            score += 15.0
        elif split_difference <= 15.0:
            score += 8.0
        else:
            score += 2.0

        if len(values) >= 1200:
            score += 10.0

        return min(100.0, score)

    @staticmethod
    def _recommend_ftp(
        ftp_95: float,
        intervals_ftp: float | None,
    ) -> float:
        """Combina el test y eFTP solo cuando la discrepancia es razonable."""

        if intervals_ftp is None:
            return round(ftp_95, 1)

        mean = (ftp_95 + intervals_ftp) / 2
        difference = abs(ftp_95 - intervals_ftp) / mean * 100 if mean else 100

        if difference <= 5.0:
            return round((ftp_95 * 0.6) + (intervals_ftp * 0.4), 1)
        if difference <= 10.0:
            return round((ftp_95 * 0.7) + (intervals_ftp * 0.3), 1)

        return round(ftp_95, 1)

    @staticmethod
    def _build_message(
        *,
        status: str,
        power: float,
        ftp_95: float,
        ftp_recommended: float | None,
        coverage: float,
        power_source: str,
        split_difference: float | None,
        intervals_ftp: float | None,
    ) -> str:
        """Genera un diagnóstico legible para Home Assistant."""

        status_text = {
            "valid": "válido",
            "partial": "parcial",
            "invalid": "inválido",
        }.get(status, status)

        source_text = "potencia del potenciómetro" if power_source == "measured" else "potencia estimada"
        message = (
            f"Test {status_text}: bloque de 20 min a {round(power)} W; "
            f"FTP 20×0,95 = {ftp_95} W; cobertura {coverage * 100:.1f}%; "
            f"fuente: {source_text}."
        )

        if split_difference is not None:
            message += f" Diferencia inicio/final: {split_difference:.1f}%."

        if intervals_ftp is not None:
            message += f" eFTP Intervals.icu: {intervals_ftp:.1f} W."

        if ftp_recommended is not None:
            message += (
                f" FTP recomendado informativo: {ftp_recommended:.1f} W. "
            )
        else:
            message += " No se recomienda actualizar el FTP con este resultado. "

        message += "No se modifica el FTP real automáticamente."
        return message

    # ------------------------------------------------------------
    # UTILIDADES
    # ------------------------------------------------------------

    @staticmethod
    def _window_average(values: list[float]) -> float | None:
        if not values:
            return None
        return fmean(values)

    @staticmethod
    def _dominant_power_source(
        window: list[tuple[int, float | None, str]],
    ) -> str:
        measured = sum(1 for _, power, source in window if power is not None and source == "measured")
        estimated = sum(1 for _, power, source in window if power is not None and source == "estimated")
        return "measured" if measured >= estimated else "estimated"

    @staticmethod
    def _safe_positive(
        value: float | int | None,
        *,
        allow_zero: bool = False,
    ) -> float | None:
        """Normaliza valores numéricos."""

        if value is None:
            return None

        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        if not isfinite(number):
            return None

        if allow_zero:
            return number if number >= 0 else None

        return number if number > 0 else None
