"""Mensaje FileId."""

from __future__ import annotations

import time

from .definitions import (
    FileType,
    Manufacturer,
    MessageNumber,
)
from .message import (
    FitField,
    FitMessage,
)


class FileIdMessage(FitMessage):
    """Mensaje FileId."""

    def __init__(self) -> None:

        fit_epoch = 631065600
        timestamp = int(time.time()) - fit_epoch

        # Identificador no nulo para el FIT generado por Coach AI.
        serial_number = 1

        super().__init__(
            local_message=0,
            global_message=MessageNumber.FILE_ID,
            fields=[
                FitField(0, FileType.WORKOUT),
                FitField(1, Manufacturer.DEVELOPMENT),
                FitField(2, 1),
                FitField(3, serial_number),
                FitField(4, timestamp),
            ],
        )