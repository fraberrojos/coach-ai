from __future__ import annotations

from pathlib import Path

from .fit_builder import FitBuilder
from .fit_writer import FitWriter
from .garmin_builder import GarminBuilder
from .models import TrainingPlan
import logging
_LOGGER = logging.getLogger(__name__)


class WorkoutExporter:
    """Exportador de entrenamientos."""

    def __init__(self) -> None:
        self.garmin_builder = GarminBuilder()
        self.fit_builder = FitBuilder()
        self.fit_writer = FitWriter()

    def export_json(
        self,
        training: TrainingPlan,
    ) -> dict:
        ...
        # deja aquí exactamente el método que ya tienes

    def save_fit(
        self,
        training: TrainingPlan,
    ) -> str:
        """Genera un archivo FIT."""
    
        _LOGGER.debug("========== WORKOUT EXPORTER DEBUG ==========")
        _LOGGER.debug("TRAINING RECIBIDO: %r", training)
        _LOGGER.debug(
            "TRAINING INTERVALS RECIBIDOS: %r",
            training.intervals,
        )
        _LOGGER.debug(
            "NUMERO DE INTERVALOS: %d",
            len(training.intervals),
        )
    
        garmin = self.garmin_builder.build(training)
    
        _LOGGER.debug(
            "GARMIN WORKOUT RESULTADO: %r",
            garmin,
        )
    
        _LOGGER.debug(
            "GARMIN STEPS RESULTADO: %r",
            garmin.steps,
        )
    
        fit = self.fit_builder.build(garmin)
    
        _LOGGER.debug(
            "FIT WORKOUT RESULTADO: %r",
            fit,
        )
    
        _LOGGER.debug(
            "FIT STEPS RESULTADO: %r",
            fit.steps,
        )
    
        folder = Path("/config/www/coach_ai")
        folder.mkdir(parents=True, exist_ok=True)
    
        filename = (
            folder
            / f"{training.workout.lower().replace(' ', '_')}.fit"
        )
    
        self.fit_writer.write(
            fit,
            filename,
        )
    
        _LOGGER.debug(
            "FIT GUARDADO EN: %s",
            filename,
        )
    
        return str(filename)