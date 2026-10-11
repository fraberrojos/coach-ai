"""Modelos de exportación."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class WorkoutStep:

    name: str

    duration: int

    target_type: str

    target_low: int | None = None

    target_high: int |None = None


@dataclass(slots=True)
class WorkoutExport:

    name: str

    description: str

    sport: str

    steps: list[WorkoutStep]