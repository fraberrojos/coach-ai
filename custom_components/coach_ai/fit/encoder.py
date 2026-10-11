"""Encoder FIT."""

from __future__ import annotations

import logging

from .binary import FitBinaryWriter
from .crc import FitCRC
from .header import FitHeader
from .messages import (
    FILE_ID_DEFINITION,
    WORKOUT_DEFINITION,
    WORKOUT_STEP_DEFINITION,
)
from .serializer import FitSerializer
from .file_id_message import FileIdMessage
from .workout_message import WorkoutMessage
from .workout_step_message import WorkoutStepMessage
from .fit_validator import FitValidator

_LOGGER = logging.getLogger(__name__)


class FitEncoder:
    """Codificador FIT."""

    def __init__(self) -> None:
        self.header = FitHeader()
        self.serializer = FitSerializer()
        self.validator = FitValidator()

    def encode(
        self,
        workout,
    ) -> bytes:
        """Genera un archivo FIT."""

        data = self.serialize_messages(
            workout,
        )

        output = FitBinaryWriter()

        self.header.write(
            output,
            len(data),
        )

        output.write_bytes(data)

        crc = FitCRC.calculate(
            output.data,
        )

        output.write_uint16(crc)

        _LOGGER.debug(
            "FIT ENCODED: %d bytes",
            len(output.data),
        )

        return output.data

    def build_messages(
        self,
        workout,
    ) -> list:
        """Construye los mensajes FIT."""

        _LOGGER.debug(
            "FIT BUILD: workout=%s steps=%d",
            workout.name,
            len(workout.steps),
        )

        messages = [
            FileIdMessage(),
            WorkoutMessage(
                workout.name,
                len(workout.steps),
            ),
        ]

        for index, step in enumerate(workout.steps):
            messages.append(
                WorkoutStepMessage(
                    index,
                    step,
                )
            )

        return messages

    def build_definitions(self) -> list:
        """Devuelve las definiciones FIT."""

        return [
            FILE_ID_DEFINITION,
            WORKOUT_DEFINITION,
            WORKOUT_STEP_DEFINITION,
        ]

    def serialize_messages(
        self,
        workout,
    ) -> bytes:
        """Serializa los mensajes FIT."""

        self.serializer.writer.clear()

        # --------------------------------------------------
        # Definition Messages
        # --------------------------------------------------

        definitions = self.build_definitions()

        for definition in definitions:
            self.serializer.serialize_definition(
                definition,
            )

        # --------------------------------------------------
        # Data Messages
        # --------------------------------------------------

        messages = self.build_messages(
            workout,
        )

        definitions_by_global = {
            FILE_ID_DEFINITION.global_message:
                FILE_ID_DEFINITION,

            WORKOUT_DEFINITION.global_message:
                WORKOUT_DEFINITION,

            WORKOUT_STEP_DEFINITION.global_message:
                WORKOUT_STEP_DEFINITION,
        }

        for message in messages:

            definition = definitions_by_global[
                message.global_message
            ]

            self.serializer.serialize(
                definition,
                message,
            )

            self.validator.validate(
                definition,
                message,
            )

        return self.serializer.writer.data

    def serialize_definitions(self) -> None:
        """Serializa las definiciones FIT."""

        self.serializer.serialize_definition(
            FILE_ID_DEFINITION,
        )

        self.serializer.serialize_definition(
            WORKOUT_DEFINITION,
        )

        self.serializer.serialize_definition(
            WORKOUT_STEP_DEFINITION,
        )