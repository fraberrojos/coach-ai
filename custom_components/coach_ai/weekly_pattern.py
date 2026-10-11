"""Patrones semanales de entrenamiento."""

from __future__ import annotations


class WeeklyPattern:
    """Patrones de entrenamiento semanales."""

    FTP = [
        "rest",
        "sweet spot",
        "endurance",
        "rest",
        "threshold",
        "endurance",
        "recovery",
    ]

    VO2 = [
        "rest",
        "vo2 max",
        "endurance",
        "rest",
        "sweet spot",
        "endurance",
        "recovery",
    ]

    ENDURANCE = [
        "rest",
        "endurance",
        "endurance",
        "rest",
        "tempo",
        "long ride",
        "recovery",
    ]

    WEIGHT_LOSS = [
        "rest",
        "endurance",
        "tempo",
        "rest",
        "endurance",
        "long ride",
        "recovery",
    ]