"""Mensaje Workout."""

from __future__ import annotations

from .definitions import (
    MessageNumber,
    Sport,
    WorkoutField,
)

from .message import (
    FitField,
    FitMessage,
)


class WorkoutMessage(FitMessage):
    """Mensaje Workout."""

    def __init__(
        self,
        name: str,
        steps: int,
    ) -> None:

        super().__init__(
            local_message=1,
            global_message=MessageNumber.WORKOUT,
            fields=[
                FitField(
                    WorkoutField.SPORT,
                    Sport.CYCLING,
                ),

                FitField(
                    WorkoutField.CAPABILITIES,
                    0,
                ),

                FitField(
                    WorkoutField.NUM_VALID_STEPS,
                    steps,
                ),

                FitField(
                    WorkoutField.WORKOUT_NAME,
                    name,
                ),

                FitField(
                    WorkoutField.SUB_SPORT,
                    0,
                ),
            ],
        )