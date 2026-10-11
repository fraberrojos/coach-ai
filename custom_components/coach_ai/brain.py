"""Cerebro principal de Coach AI."""

from __future__ import annotations


class BrainEngine:
    """Combina todos los motores."""

    def think(
        self,
        recovery: int,
        fitness: str,
        fatigue: str,
        readiness: str,
        risk: str,
        confidence: int,
        consistency: int,
        performance: int,
    ) -> str:

        score = 0

        score += recovery

        score += consistency // 2

        score += performance // 2

        score += confidence // 4

        if fitness == "race_ready":
            score += 15
        elif fitness == "fit":
            score += 8

        if fatigue == "Muy alta":
            score -= 20

        if risk == "critical":
            score -= 40

        if readiness == "Peak":
            score += 15

        if score >= 170:
            return "GO HARD"

        if score >= 140:
            return "TRAIN"

        if score >= 100:
            return "EASY"

        return "REST"