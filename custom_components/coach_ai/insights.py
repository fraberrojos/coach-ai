"""Generador de explicaciones de Coach AI."""

from __future__ import annotations


class InsightEngine:
    """Genera mensajes inteligentes."""

    def build(
        self,
        recovery: int,
        fitness: str,
        fatigue: str,
        recommendation: str,
    ) -> list[str]:

        messages: list[str] = []

        if recovery >= 85:
            messages.append(
                "Excelente recuperación. Es un gran día para exigir al cuerpo."
            )

        elif recovery >= 65:
            messages.append(
                "Recuperación adecuada para entrenar con normalidad."
            )

        elif recovery >= 40:
            messages.append(
                "Conviene reducir la intensidad y priorizar la calidad."
            )

        else:
            messages.append(
                "La recuperación es baja. Descansar hoy mejorará el rendimiento futuro."
            )

        if fitness == "race_ready":
            messages.append(
                "Tu estado de forma está cerca del máximo."
            )

        elif fitness == "fit":
            messages.append(
                "El estado de forma es sólido y continúa mejorando."
            )

        elif fitness == "building":
            messages.append(
                "Todavía estás construyendo la base aeróbica."
            )

        elif fitness == "detrained":
            messages.append(
                "Es necesario recuperar continuidad en los entrenamientos."
            )

        if fatigue == "Muy alta":
            messages.append(
                "La fatiga acumulada aconseja un día suave."
            )

        messages.append(
            f"Recomendación: {recommendation}."
        )

        return messages