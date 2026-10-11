"""Predicción de carga de entrenamiento."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ForecastDay:
    """Estado previsto de un día."""

    ctl: float
    atl: float
    tsb: float
    tss: int


class ForecastEngine:
    """Predice la evolución de la carga."""

    def simulate(
        self,
        ctl: float,
        atl: float,
        daily_tss: list[int],
    ) -> list[ForecastDay]:
        """Simula varios días."""

        forecast: list[ForecastDay] = []

        current_ctl = ctl
        current_atl = atl

        for tss in daily_tss:

            current_ctl = current_ctl + (tss - current_ctl) / 42
            current_atl = current_atl + (tss - current_atl) / 7

            forecast.append(
                ForecastDay(
                    ctl=round(current_ctl, 1),
                    atl=round(current_atl, 1),
                    tsb=round(current_ctl - current_atl, 1),
                    tss=tss,
                )
            )

        return forecast

    def tomorrow(
        self,
        recovery: int,
        fatigue: str,
        risk: str,
    ) -> int:
        """Predice la recuperación de mañana."""

        score = recovery

        if fatigue == "Muy alta":
            score += 12
        elif fatigue == "Alta":
            score += 8
        elif fatigue == "Media":
            score += 4
        else:
            score += 2

        if risk == "high":
            score += 3
        elif risk == "low":
            score += 1

        return max(0, min(100, score))