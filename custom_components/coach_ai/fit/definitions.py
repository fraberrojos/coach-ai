"""Definiciones oficiales FIT usadas por Coach AI."""

from __future__ import annotations

from enum import IntEnum


# ==========================================================
# File types
# ==========================================================

class FileType(IntEnum):
    DEVICE = 1
    SETTINGS = 2
    SPORT = 3
    ACTIVITY = 4
    WORKOUT = 5


# ==========================================================
# Sport
# ==========================================================

class Sport(IntEnum):
    GENERIC = 0
    RUNNING = 1
    CYCLING = 2


# ==========================================================
# Manufacturer
# ==========================================================

class Manufacturer(IntEnum):
    GARMIN = 1
    DEVELOPMENT = 255


# ==========================================================
# Workout step intensity
# ==========================================================

class Intensity(IntEnum):
    ACTIVE = 0
    REST = 1
    WARMUP = 2
    COOLDOWN = 3


# ==========================================================
# Duration type
# ==========================================================

class DurationType(IntEnum):
    TIME = 0


# ==========================================================
# Workout step target type
# ==========================================================

class TargetType(IntEnum):
    SPEED = 0
    HEART_RATE = 1
    OPEN = 2
    CADENCE = 3
    POWER = 4


# ==========================================================
# Message Numbers (FIT Profile)
# ==========================================================

class MessageNumber(IntEnum):
    FILE_ID = 0
    WORKOUT = 26
    WORKOUT_STEP = 27
    FILE_CREATOR = 49


# ==========================================================
# Base Types
# ==========================================================

class BaseType(IntEnum):
    ENUM = 0x00
    SINT8 = 0x01
    UINT8 = 0x02
    SINT16 = 0x83
    UINT16 = 0x84
    SINT32 = 0x85
    UINT32 = 0x86
    STRING = 0x07
    FLOAT32 = 0x88
    FLOAT64 = 0x89
    UINT8Z = 0x0A
    UINT16Z = 0x8B
    UINT32Z = 0x8C
    BYTE = 0x0D


# ==========================================================
# Local Message Numbers
# ==========================================================

class LocalMessage(IntEnum):
    FILE_ID = 0
    WORKOUT = 1
    WORKOUT_STEP = 2


# ==========================================================
# FileId fields
# ==========================================================

class FileIdField(IntEnum):
    TYPE = 0
    MANUFACTURER = 1
    PRODUCT = 2
    SERIAL_NUMBER = 3
    TIME_CREATED = 4
    NUMBER = 5
    PRODUCT_NAME = 7


# ==========================================================
# Workout fields
# ==========================================================

class WorkoutField(IntEnum):
    SPORT = 4
    CAPABILITIES = 5
    NUM_VALID_STEPS = 6
    WORKOUT_NAME = 8

    SUB_SPORT = 11
    POOL_LENGTH = 14
    POOL_LENGTH_UNIT = 15

    ENABLED = 16
    WKT_DESCRIPTION = 17
    WKT_TYPE = 18
    CONNECTIQ_APP_ID = 19
    SPORT_FLAGS = 20


# ==========================================================
# WorkoutStep fields
# ==========================================================

class WorkoutStepField(IntEnum):
    MESSAGE_INDEX = 254
    WKT_STEP_NAME = 0

    DURATION_TYPE = 1
    DURATION_VALUE = 2

    TARGET_TYPE = 3
    TARGET_VALUE = 4

    CUSTOM_TARGET_LOW = 5
    CUSTOM_TARGET_HIGH = 6

    INTENSITY = 7

    NOTES = 8
    EQUIPMENT = 9
    EXERCISE_CATEGORY = 10
    EXERCISE_NAME = 11
    EXERCISE_WEIGHT = 12
    WEIGHT_DISPLAY_UNIT = 13
    SECONDARY_TARGET = 14
    SECONDARY_TARGET_VALUE = 15


# ==========================================================
# FileCreator fields
# ==========================================================

class FileCreatorField(IntEnum):
    """Campos FileCreator."""

    SOFTWARE_VERSION = 0
    HARDWARE_VERSION = 1


# ==========================================================
# Definition Field
# ==========================================================

class DefinitionField:
    """Campo de una definición FIT."""

    def __init__(
        self,
        number: int,
        size: int,
        base_type: int,
    ) -> None:
        self.number = number
        self.size = size
        self.base_type = base_type