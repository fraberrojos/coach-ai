"""Mensajes FIT."""

from __future__ import annotations

from dataclasses import dataclass

from .definitions import (
    BaseType,
    DefinitionField,
    FileIdField,
    MessageNumber,
    WorkoutField,
    WorkoutStepField,
)


@dataclass(slots=True)
class MessageDefinition:
    """Define un mensaje FIT."""

    local_message: int
    global_message: int
    fields: list[DefinitionField]


# ==========================================================
# FILE_ID
# ==========================================================

FILE_ID_DEFINITION = MessageDefinition(
    local_message=0,
    global_message=MessageNumber.FILE_ID,
    fields=[
        DefinitionField(
            FileIdField.TYPE,
            1,
            BaseType.ENUM,
        ),
        DefinitionField(
            FileIdField.MANUFACTURER,
            2,
            BaseType.UINT16,
        ),
        DefinitionField(
            FileIdField.PRODUCT,
            2,
            BaseType.UINT16,
        ),
        DefinitionField(
            FileIdField.SERIAL_NUMBER,
            4,
            BaseType.UINT32,
        ),
        DefinitionField(
            FileIdField.TIME_CREATED,
            4,
            BaseType.UINT32,
        ),
    ],
)


# ==========================================================
# WORKOUT
# ==========================================================

WORKOUT_DEFINITION = MessageDefinition(
    local_message=1,
    global_message=MessageNumber.WORKOUT,
    fields=[
        DefinitionField(
            WorkoutField.SPORT,
            1,
            BaseType.ENUM,
        ),
        DefinitionField(
            WorkoutField.CAPABILITIES,
            4,
            BaseType.UINT32,
        ),
        DefinitionField(
            WorkoutField.NUM_VALID_STEPS,
            2,
            BaseType.UINT16,
        ),
        DefinitionField(
            WorkoutField.WORKOUT_NAME,
            16,
            BaseType.STRING,
        ),
        DefinitionField(
            WorkoutField.SUB_SPORT,
            1,
            BaseType.ENUM,
        ),
    ],
)


# ==========================================================
# WORKOUT_STEP
# ==========================================================

WORKOUT_STEP_DEFINITION = MessageDefinition(
    local_message=2,
    global_message=MessageNumber.WORKOUT_STEP,
    fields=[
        DefinitionField(
            WorkoutStepField.MESSAGE_INDEX,
            2,
            BaseType.UINT16,
        ),
        DefinitionField(
            WorkoutStepField.WKT_STEP_NAME,
            16,
            BaseType.STRING,
        ),
        DefinitionField(
            WorkoutStepField.DURATION_TYPE,
            1,
            BaseType.ENUM,
        ),
        DefinitionField(
            WorkoutStepField.DURATION_VALUE,
            4,
            BaseType.UINT32,
        ),
        DefinitionField(
            WorkoutStepField.TARGET_TYPE,
            1,
            BaseType.ENUM,
        ),
        DefinitionField(
            WorkoutStepField.TARGET_VALUE,
            4,
            BaseType.UINT32,
        ),
        DefinitionField(
            WorkoutStepField.CUSTOM_TARGET_LOW,
            4,
            BaseType.UINT32,
        ),
        DefinitionField(
            WorkoutStepField.CUSTOM_TARGET_HIGH,
            4,
            BaseType.UINT32,
        ),
        DefinitionField(
            WorkoutStepField.INTENSITY,
            1,
            BaseType.ENUM,
        ),
        
    ],
)