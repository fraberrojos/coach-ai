"""Exportador semanal de entrenamientos."""

from __future__ import annotations

from pathlib import Path

from .workout_exporter import WorkoutExporter


class WeeklyWorkoutExporter:
    """Exporta una semana completa."""

    def __init__(self) -> None:
        self.exporter = WorkoutExporter()

    def export(
        self,
        week: list,
        folder: Path,
    ) -> list[Path]:

        files = []

        for training in week:
            files.append(
                self.exporter.save_fit(
                    training,
                    folder,
                )
            )

        return files