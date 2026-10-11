"""Botones de Coach AI."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .entity import CoachAIEntity

_LOGGER = logging.getLogger(__name__)


class CoachAIAnalyzeButton(CoachAIEntity, ButtonEntity):
    """Botón para forzar un nuevo análisis de Athena y recalcular la semana."""

    _attr_name = "Analyze Now"
    _attr_unique_id = "coach_ai_analyze_now"
    _attr_icon = "mdi:brain"

    def __init__(self, coordinator):
        """Inicializa el botón."""
        super().__init__(coordinator)

    async def async_press(self) -> None:
        """Fuerza el recálculo completo sin depender de Garmin."""
        try:
            await self.coordinator.async_recalculate_week()
        except Exception:
            _LOGGER.exception(
                "Coach AI: error al ejecutar el recálculo manual de Athena/semana."
            )
            raise


class CoachAIFTCTestButton(CoachAIEntity, ButtonEntity):
    """Botón para generar y programar el test FTP."""

    _attr_name = "Test FTP"
    _attr_unique_id = "coach_ai_ftp_test"
    _attr_icon = "mdi:flask-outline"

    async def async_press(self) -> None:
        """Genera el test y lo programa en Garmin para mañana."""
        try:
            await self.coordinator.async_start_ftp_test()
        except Exception:
            _LOGGER.exception("Coach AI: error al generar/programar el test FTP.")
            raise


class CoachAIFTCPendingResultButton(CoachAIEntity, ButtonEntity):
    """Registra el resultado manual provisional del test FTP."""

    _attr_name = "Registrar FTP provisional"
    _attr_unique_id = "coach_ai_ftp_register_provisional"
    _attr_icon = "mdi:clipboard-check-outline"

    @property
    def available(self) -> bool:
        """Solo está disponible mientras el resultado no sea provisional."""
        return self.coordinator._ftp_test_result.get("status") != "provisional"

    async def async_press(self) -> None:
        """Guarda el resultado provisional sin modificar el FTP de Garmin."""
        try:
            await self.coordinator.async_register_manual_ftp_result(
                power_20min=145.0,
                ftp_95=137.8,
            )
        except Exception:
            _LOGGER.exception(
                "Coach AI: error al registrar el resultado FTP provisional."
            )
            raise


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
):
    """Configura los botones."""

    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            CoachAIAnalyzeButton(coordinator),
            CoachAIFTCTestButton(coordinator),
            CoachAIFTCPendingResultButton(coordinator),
        ]
    )
