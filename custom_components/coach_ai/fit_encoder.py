"""Codificador de entrenamientos FIT."""

from __future__ import annotations

from .fit_models import FitWorkout


class FitEncoder:
    """Convierte un FitWorkout en un archivo FIT."""

    def encode(
        self,
        workout: FitWorkout,
    ) -> bytes:
        """Genera el contenido binario del archivo FIT."""

        # TODO:
        # Implementar el protocolo FIT oficial.
        # De momento devolvemos un binario válido para las pruebas
        # de integración entre módulos.

        data = bytearray()

        data.extend(workout.name.encode("utf-8"))
        data.extend(b"\x00")

        for step in workout.steps:
            data.extend(step.name.encode("utf-8"))
            data.extend(b"\x00")

        return bytes(data)