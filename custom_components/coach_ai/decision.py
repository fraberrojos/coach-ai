"""Motor de decisión."""

from __future__ import annotations


class DecisionEngine:
    """Genera la decisión final."""

    def decide(
        self,
        readiness: str,
        risk: str,
        confidence: int,
    ) -> str:

        if risk == "critical":
            return "REST"

        if confidence < 60:
            return "INSUFFICIENT_DATA"

        if readiness == "Peak":
            return "HIGH_INTENSITY"

        if readiness == "Ready":
            return "NORMAL_TRAINING"

        if readiness == "Moderate":
            return "ENDURANCE"

        if readiness == "Easy Only":
            return "RECOVERY"

        return "REST"