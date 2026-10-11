"""Experiencia acumulada."""

from __future__ import annotations


class ExperienceEngine:
    """Evalúa la experiencia acumulada."""

    def analyse(
        self,
        history: list[dict],
    ) -> tuple[int, str]:

        days = len(history)

        if days < 7:
            return 10, "Nuevo usuario"

        if days < 30:
            return 30, "Aprendiendo hábitos"

        if days < 90:
            return 60, "Conociendo al deportista"

        if days < 180:
            return 85, "Perfil consolidado"

        return 100, "Perfil totalmente aprendido"