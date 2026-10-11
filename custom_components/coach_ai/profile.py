"""Perfil del deportista."""

from __future__ import annotations


class ProfileEngine:
    """Clasifica el nivel del deportista."""

    def classify(
        self,
        athlete,
    ) -> str:

        ctl = athlete.ctl or 0

        if ctl < 20:
            return "beginner"

        if ctl < 45:
            return "intermediate"

        if ctl < 75:
            return "advanced"

        return "elite"