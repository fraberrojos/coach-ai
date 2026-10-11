"""Mensaje WorkoutStep."""

from __future__ import annotations

from .definitions import (
    DurationType,
    Intensity,
    MessageNumber,
    TargetType,
    WorkoutStepField,
)

from .message import (
    FitField,
    FitMessage,
)

from ..fit_models import FitStep


class WorkoutStepMessage(FitMessage):
    """Mensaje WorkoutStep."""

    def __init__(
        self,
        index: int,
        step: FitStep,
    ) -> None:

        # --------------------------------------------------
        # TARGET TYPE
        # --------------------------------------------------

        target = TargetType.OPEN

        if step.target_type == "power":
            target = TargetType.POWER

        elif step.target_type == "heart_rate":
            target = TargetType.HEART_RATE

        elif step.target_type == "cadence":
            target = TargetType.CADENCE

        # --------------------------------------------------
        # INTENSITY
        # --------------------------------------------------

        intensity = Intensity.ACTIVE

        if step.intensity == "rest":
            intensity = Intensity.REST

        elif step.intensity == "warmup":
            intensity = Intensity.WARMUP

        elif step.intensity == "cooldown":
            intensity = Intensity.COOLDOWN

        # --------------------------------------------------
        # TARGET VALUES
        # --------------------------------------------------

        target_value = 0
        target_low = 0
        target_high = 0

        if step.target_low is not None:

            if (
                step.target_high is not None
                and step.target_low == step.target_high
            ):
                # Objetivo único.
                #
                # Ejemplo:
                # CADENCE = 90
                target_value = step.target_low

            else:
                # Rango.
                target_low = step.target_low

                if step.target_high is not None:
                    target_high = step.target_high
                else:
                    target_high = step.target_low

        # --------------------------------------------------
        # MENSAJE FIT
        # --------------------------------------------------

        super().__init__(
            local_message=2,
            global_message=MessageNumber.WORKOUT_STEP,
            fields=[
                FitField(
                    WorkoutStepField.MESSAGE_INDEX,
                    index,
                ),

                FitField(
                    WorkoutStepField.WKT_STEP_NAME,
                    step.name,
                ),

                FitField(
                    WorkoutStepField.DURATION_TYPE,
                    DurationType.TIME,
                ),

                FitField(
                    WorkoutStepField.DURATION_VALUE,
                    step.duration * 60 * 1000,
                ),

                FitField(
                    WorkoutStepField.TARGET_TYPE,
                    target,
                ),

                FitField(
                    WorkoutStepField.TARGET_VALUE,
                    target_value,
                ),

                FitField(
                    WorkoutStepField.CUSTOM_TARGET_LOW,
                    target_low,
                ),

                FitField(
                    WorkoutStepField.CUSTOM_TARGET_HIGH,
                    target_high,
                ),

                FitField(
                    WorkoutStepField.INTENSITY,
                    intensity,
                ),
            ],
        )