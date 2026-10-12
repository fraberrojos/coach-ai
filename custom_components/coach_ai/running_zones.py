"""Zonas específicas de carrera a pie.

El ritmo umbral se expresa en segundos por kilómetro. No se usan FTP ni
zonas de potencia de ciclismo para calcular zonas de running.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RunningZone:
    """Zona de carrera con límites de ritmo y, opcionalmente, pulso."""

    name: str
    pace_min_sec_km: int | None
    pace_max_sec_km: int | None
    hr_min: int | None = None
    hr_max: int | None = None


class RunningZones:
    """Calcula zonas de ritmo a partir del ritmo umbral y zonas de pulso."""

    PACE_FACTORS: dict[str, tuple[float | None, float | None]] = {
        "recovery": (1.25, 1.50),
        "easy": (1.12, 1.25),
        "endurance": (1.06, 1.12),
        "tempo": (0.98, 1.06),
        "threshold": (0.95, 1.00),
        "interval": (0.85, 0.95),
        "repetition": (None, 0.85),
    }

    def __init__(self, threshold_pace_sec_km: int | None = None, max_hr: int | None = None) -> None:
        if threshold_pace_sec_km is not None and threshold_pace_sec_km <= 0:
            raise ValueError("El ritmo umbral debe ser mayor que cero.")
        if max_hr is not None and not 80 <= max_hr <= 240:
            raise ValueError("La frecuencia cardíaca máxima no es válida.")
        self.threshold_pace_sec_km = threshold_pace_sec_km
        self.max_hr = max_hr

    def pace_range(self, zone: str) -> tuple[int | None, int | None]:
        """Devuelve (ritmo más rápido, ritmo más lento), en segundos/km."""
        key = zone.strip().lower()
        if key not in self.PACE_FACTORS:
            raise ValueError(f"Zona de running desconocida: {zone}")
        if self.threshold_pace_sec_km is None:
            return None, None
        fast_factor, slow_factor = self.PACE_FACTORS[key]
        fast = round(self.threshold_pace_sec_km * fast_factor) if fast_factor is not None else None
        slow = round(self.threshold_pace_sec_km * slow_factor) if slow_factor is not None else None
        return fast, slow

    def heart_rate_range(self, zone: str) -> tuple[int | None, int | None]:
        """Devuelve límites aproximados por porcentaje de FC máxima."""
        if self.max_hr is None:
            return None, None
        ranges = {
            "recovery": (0.50, 0.60), "easy": (0.60, 0.70),
            "endurance": (0.65, 0.75), "tempo": (0.75, 0.85),
            "threshold": (0.85, 0.92), "interval": (0.92, 0.97),
            "repetition": (0.97, 1.00),
        }
        key = zone.strip().lower()
        if key not in ranges:
            raise ValueError(f"Zona de running desconocida: {zone}")
        low, high = ranges[key]
        return round(self.max_hr * low), round(self.max_hr * high)
