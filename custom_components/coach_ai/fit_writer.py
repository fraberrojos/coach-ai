"""Escritor de archivos FIT."""

from __future__ import annotations

import logging
from pathlib import Path

from .fit.encoder import FitEncoder
from .fit_models import FitWorkout
from .fit.fit_parser import FitParser

_LOGGER = logging.getLogger(__name__)

class FitWriter:
    def write(self, workout: FitWorkout, filename: str | Path) -> None:
        """Codifica y escribe un entrenamiento FIT."""
        encoder = FitEncoder()
        _LOGGER.debug("FitWriter.write(): workout=%s | steps=%d", getattr(workout, "name", None), len(getattr(workout, "steps", []) or []))
        data = encoder.encode(workout)
        Path("/config/coach.fit").write_bytes(data)
        Path(filename).write_bytes(data)
        _LOGGER.info("FIT generado correctamente | archivo=%s | bytes=%d", filename, len(data))
        try:
            FitParser(data).parse()
        except Exception:
            _LOGGER.debug("FIT generado, pero el parser de diagnóstico no pudo inspeccionarlo.", exc_info=True)
        garmin = Path("/config/garmin.fit")
        if garmin.exists():
            try:
                FitParser(garmin.read_bytes()).parse()
            except Exception:
                _LOGGER.debug("No se pudo inspeccionar el FIT de referencia Garmin.", exc_info=True)
