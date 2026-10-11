"""Perfil FIT para Coach AI."""

from __future__ import annotations

from enum import IntEnum


class FileType(IntEnum):
    DEVICE = 1
    SETTINGS = 2
    SPORT = 3
    ACTIVITY = 4
    WORKOUT = 5
    COURSE = 6


class Sport(IntEnum):
    CYCLING = 2


class Intensity(IntEnum):
    ACTIVE = 0
    REST = 1
    WARMUP = 2
    COOLDOWN = 3


class DurationType(IntEnum):
    TIME = 0


class TargetType(IntEnum):
    OPEN = 0
    HEART_RATE = 1
    POWER = 2
    CADENCE = 3