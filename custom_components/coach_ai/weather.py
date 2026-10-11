"""Weather Engine de Coach AI."""

from __future__ import annotations

from .models import AthleteState


class WeatherEngine:
    """Analiza las condiciones meteorológicas."""

    def recommend(
        self,
        athlete: AthleteState,
    ) -> tuple[bool, str]:
        """
        Devuelve:
            (outdoor, motivo)
        """

        if athlete.raining:
            return (
                False,
                "Lluvia detectada.",
            )

        if athlete.wind_speed is not None:

            if athlete.wind_speed > 35:
                return (
                    False,
                    "Viento muy fuerte.",
                )

            if athlete.wind_speed > 25:
                return (
                    True,
                    "Viento moderado. Reduce la intensidad.",
                )

        if athlete.temperature is not None:

            if athlete.temperature < 0:
                return (
                    False,
                    "Temperatura bajo cero.",
                )

            if athlete.temperature > 38:
                return (
                    False,
                    "Temperatura extrema.",
                )

        return (
            True,
            "Condiciones favorables.",
        )