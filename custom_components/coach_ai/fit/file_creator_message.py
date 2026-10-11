"""Mensaje FileCreator."""

from __future__ import annotations

from .definitions import (
    FileCreatorField,
    MessageNumber,
)
from .message import (
    FitField,
    FitMessage,
)


class FileCreatorMessage(FitMessage):
    """Mensaje FileCreator."""

    def __init__(self) -> None:

        super().__init__(
            local_message=1,
            global_message=MessageNumber.FILE_CREATOR,
            fields=[
                FitField(
                    FileCreatorField.SOFTWARE_VERSION,
                    100,
                ),
                FitField(
                    FileCreatorField.HARDWARE_VERSION,
                    1,
                ),
            ],
        )