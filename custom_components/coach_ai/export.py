"""Exportador de entrenamientos."""

from __future__ import annotations

from pathlib import Path
from xml.etree.ElementTree import (
    Element,
    SubElement,
    ElementTree,
)

from .models import TrainingPlan


class ZwiftExporter:
    """Genera archivos .zwo."""

    def export(
        self,
        training: TrainingPlan,
        filename: str,
    ) -> Path:
        """Exporta un entrenamiento a formato Zwift."""

        root = Element("workout_file")

        name = SubElement(root, "name")
        name.text = training.workout

        author = SubElement(root, "author")
        author.text = "Coach AI"

        description = SubElement(root, "description")
        description.text = training.reason

        workout = SubElement(root, "workout")

        ftp = training.target_power or 200

        for interval in training.intervals:

            power = interval.power or ftp

            intensity = round(power / ftp, 3)

            if interval.name.lower().startswith("rec"):

                tag = "SteadyState"

            elif interval.name.lower().startswith("cal"):

                tag = "Warmup"

            elif interval.name.lower().startswith("enf"):

                tag = "Cooldown"

            else:

                tag = "SteadyState"

            SubElement(
                workout,
                tag,
                Duration=str(interval.duration * 60),
                Power=str(intensity),
            )

        path = Path(filename)

        ElementTree(root).write(
            path,
            encoding="utf-8",
            xml_declaration=True,
        )

        return path