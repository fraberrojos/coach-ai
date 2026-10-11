"""Exportador de entrenamientos."""

from __future__ import annotations

import json
from pathlib import Path

from homeassistant.core import HomeAssistant

from .export_models import WorkoutExport


class WorkoutExporter:
    """Exporta entrenamientos."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def export_json(
        self,
        workout: WorkoutExport,
        filename: str = "coach_ai_workout.json",
    ) -> str:
        """Exporta el entrenamiento a JSON."""

        output = Path(self.hass.config.path("www")) / filename

        data = {
            "name": workout.name,
            "description": workout.description,
            "sport": workout.sport,
            "steps": [
                {
                    "name": step.name,
                    "duration": step.duration,
                    "target_type": step.target_type,
                    "target_low": step.target_low,
                    "target_high": step.target_high,
                }
                for step in workout.steps
            ],
        }

        output.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )

        return str(output)