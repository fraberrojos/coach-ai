"""Validador de mensajes FIT."""

from __future__ import annotations

from .message import FitMessage
from .messages import MessageDefinition


class FitValidator:
    """Valida mensajes FIT."""

    def validate(
        self,
        definition: MessageDefinition,
        message: FitMessage,
    ) -> None:

        values = message.field_map()

        expected = [
            field.number
            for field in definition.fields
        ]

        received = sorted(values.keys())

        missing = [
            number
            for number in expected
            if number not in values
        ]

        extra = [
            number
            for number in received
            if number not in expected
        ]

        if missing or extra:

            raise ValueError(
                "\n"
                f"Mensaje : {type(message).__name__}\n"
                f"Espera  : {expected}\n"
                f"Tiene   : {received}\n"
                f"Faltan  : {missing}\n"
                f"Sobran  : {extra}"
            )