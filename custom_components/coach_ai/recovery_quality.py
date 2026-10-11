"""Calidad de recuperación."""

from __future__ import annotations


class RecoveryQualityEngine:
    """Clasifica la calidad de la recuperación."""

    def classify(
        self,
        recovery: int,
    ) -> str:

        if recovery >= 90:
            return "Excellent"

        if recovery >= 75:
            return "Good"

        if recovery >= 60:
            return "Fair"

        if recovery >= 40:
            return "Poor"

        return "Critical"